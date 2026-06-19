import requests

from django.db import transaction
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from Core.tasks import send_email_task, send_sms
from Orders.models import (
    CartItemModel,
    CartModel,
    OrderAuditLogModel,
    OrderItemModel,
    OrderModel,
)
from Orders.payment import ZarinPalClient
from Orders.serializers import (
    CartItemSerializer,
    CartItemUpdateSerializer,
    CartItemWriteSerializer,
    CartSerializer,
    CheckoutSerializer,
    OrderAuditLogSerializer,
    OrderSerializer,
    SellerOrderSerializer,
    SellerOrderStatusUpdateSerializer,
)


def get_or_create_cart(user):
    cart, _ = CartModel.objects.get_or_create(user=user)
    return cart


def build_order_address_snapshot(*, user, address):
    receiver_name = f"{user.first_name} {user.last_name}".strip()
    return {
        "receiver_name": receiver_name,
        "receiver_phone": user.phone,
        "address_title": address.title or "",
        "province": address.province,
        "city": address.city,
        "street": address.street,
        "alley": address.alley or "",
        "number": address.number,
        "unit": address.unit or "",
        "postal_code": address.postal_code,
        "full_address": address.full_address or address.build_full_address(),
    }


def get_shipping_amount(items_total):
    free_threshold = getattr(settings, "ORDER_FREE_SHIPPING_THRESHOLD", 0)
    base_amount = getattr(settings, "ORDER_DEFAULT_SHIPPING_AMOUNT", 0)
    if free_threshold and items_total >= free_threshold:
        return 0
    return base_amount


def create_order_audit_log(order, action, *, actor=None, note="", payload=None):
    return OrderAuditLogModel.objects.create(
        order=order,
        actor=actor,
        action=action,
        note=note,
        payload=payload or {},
    )


def build_order_notification_message(order, event, status_label=None):
    if event == "created":
        return (
            f"Enma Shop\nYour order {order.order_number} has been created successfully "
            f"and is waiting for payment."
        )
    if event == "paid":
        return (
            f"Enma Shop\nOrder {order.order_number} was paid successfully. "
            f"Amount: {order.payable_amount}"
        )
    if event == "processing":
        return (
            f"Enma Shop\nYour order {order.order_number} is now being prepared by the seller."
        )
    if event == "shipped":
        return f"Enma Shop\nYour order {order.order_number} has been shipped."
    if event == "delivered":
        return f"Enma Shop\nYour order {order.order_number} has been marked as delivered."
    if event == "cancelled":
        return f"Enma Shop\nYour order {order.order_number} has been cancelled."
    return (
        f"Enma Shop\nOrder {order.order_number} status changed to "
        f"{status_label or order.get_status_display()}."
    )


def get_order_sellers(order):
    seller_users = []
    seen_seller_ids = set()
    for item in order.items.filter(is_deleted=False).select_related("shop__user"):
        if item.shop and item.shop.user_id not in seen_seller_ids:
            seen_seller_ids.add(item.shop.user_id)
            seller_users.append(item.shop.user)
    return seller_users


def notify_order_parties(order, event):
    status_label = order.get_status_display()
    message = build_order_notification_message(order, event, status_label=status_label)
    buyer_phone = order.receiver_phone or order.user.phone
    buyer_email = order.user.email
    seller_users = get_order_sellers(order)

    if event == "created":
        if buyer_email:
            send_email_task.delay(buyer_email, message)
        return

    if event == "paid":
        if buyer_email:
            send_email_task.delay(buyer_email, message)
        send_sms.delay(buyer_phone, message)
        for seller in seller_users:
            seller_message = (
                f"Enma Shop\nA paid order {order.order_number} requires your attention."
            )
            if seller.email:
                send_email_task.delay(seller.email, seller_message)
            send_sms.delay(seller.phone, seller_message)
        return

    if event == "processing":
        if buyer_email:
            send_email_task.delay(buyer_email, message)
        return

    if event == "shipped":
        if buyer_email:
            send_email_task.delay(buyer_email, message)
        send_sms.delay(buyer_phone, message)
        return

    if event == "delivered":
        if buyer_email:
            send_email_task.delay(buyer_email, message)
        return

    if event == "cancelled":
        if buyer_email:
            send_email_task.delay(buyer_email, message)
        send_sms.delay(buyer_phone, message)
        return

    if buyer_email:
        send_email_task.delay(buyer_email, message)


def validate_single_shop_cart(cart_items):
    shop_ids = {item.product.shop_id for item in cart_items}
    return len(shop_ids) <= 1


def get_seller_order_queryset(user):
    return (
        OrderModel.objects.filter(
            items__shop__user=user,
            items__is_deleted=False,
            is_deleted=False,
        )
        .select_related("user", "address")
        .prefetch_related("items", "items__shop", "items__product")
        .distinct()
    )


def get_allowed_status_transitions():
    return {
        OrderModel.Status.PAID: {
            OrderModel.Status.PROCESSING,
            OrderModel.Status.CANCELLED,
        },
        OrderModel.Status.PROCESSING: {
            OrderModel.Status.SHIPPED,
            OrderModel.Status.CANCELLED,
        },
        OrderModel.Status.SHIPPED: {
            OrderModel.Status.DELIVERED,
        },
        OrderModel.Status.DELIVERED: set(),
        OrderModel.Status.CANCELLED: set(),
        OrderModel.Status.PENDING: set(),
    }


def can_transition_order_status(order, next_status):
    return next_status in get_allowed_status_transitions().get(order.status, set())


class CartView(APIView):
    def get_cart(self, user):
        return get_or_create_cart(user)

    def get(self, request):
        cart = self.get_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartItemView(APIView):
    def post(self, request):
        serializer = CartItemWriteSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        product = serializer.context["product"]
        quantity = serializer.validated_data["quantity"]  # type: ignore
        cart = get_or_create_cart(request.user)
        existing_shop_ids = set(
            cart.cart_items.values_list("product__shop_id", flat=True)  # type: ignore
        )
        if existing_shop_ids and product.shop_id not in existing_shop_ids:
            return Response(
                {
                    "detail": "Phase 1 checkout supports products from a single shop per cart."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            cart_item = CartItemModel.objects.filter(cart=cart, product=product).first()
            created = cart_item is None
            if created:
                if product.stock < quantity:
                    return Response(
                        {"detail": "Requested quantity exceeds available stock."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                cart_item = CartItemModel.objects.create(
                    cart=cart, product=product, quantity=quantity
                )
            else:
                cart_item.quantity += quantity
                if cart_item.quantity > product.stock:
                    return Response(
                        {"detail": "Requested quantity exceeds available stock."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                cart_item.save(update_fields=["quantity", "updated_at"])
        response_serializer = CartItemSerializer(cart_item)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def patch(self, request, item_id):
        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            cart_item = CartItemModel.objects.select_related("product", "cart").get(
                id=item_id,
                cart__user=request.user,
            )
        except CartItemModel.DoesNotExist:
            return Response(
                {"detail": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        quantity = serializer.validated_data["quantity"]  # type: ignore
        if cart_item.product.stock < quantity:
            return Response(
                {"detail": "Requested quantity exceeds available stock."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cart_item.quantity = quantity
        cart_item.save(update_fields=["quantity", "updated_at"])
        return Response(CartItemSerializer(cart_item).data, status=status.HTTP_200_OK)

    def delete(self, request, item_id):
        try:
            cart_item = CartItemModel.objects.get(
                id=item_id,
                cart__user=request.user,
            )
        except CartItemModel.DoesNotExist:
            return Response(
                {"detail": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CheckoutView(APIView):
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            cart = CartModel.objects.get(user=request.user)
        except CartModel.DoesNotExist:
            return Response(
                {"detail": "Cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cart_items = list(
            cart.cart_items.filter(  # type: ignore
                product__is_deleted=False,
                product__is_active=True,
                product__shop__is_deleted=False,
            ).select_related("product", "product__shop")
        )
        if not cart_items:
            return Response(
                {"detail": "Cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not validate_single_shop_cart(cart_items):
            return Response(
                {
                    "detail": "Phase 1 checkout supports products from a single shop per order."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        for item in cart_items:
            if item.quantity > item.product.stock:
                return Response(
                    {
                        "detail": f"Insufficient stock for product '{item.product.name}'."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        address = serializer.context["address"]
        address_snapshot = build_order_address_snapshot(
            user=request.user,
            address=address,
        )
        description = f"Payment for order by user {request.user.phone}"
        with transaction.atomic():
            order = OrderModel.objects.create(
                user=request.user,
                address=address,
                description=description,
                status=OrderModel.Status.PENDING,
                payment_status=OrderModel.PaymentStatus.UNPAID,
                **address_snapshot,
            )
            items_total = 0
            items_payload = []
            for item in cart_items:
                line_total = item.quantity * item.product.price
                items_total += line_total
                OrderItemModel.objects.create(
                    order=order,
                    product=item.product,
                    shop=item.product.shop,
                    product_name=item.product.name,
                    shop_name=item.product.shop.name,
                    quantity=item.quantity,
                    unit_price=item.product.price,
                    line_total=line_total,
                )
                items_payload.append(
                    {
                        "item_name": item.product.name,
                        "item_amount": item.product.price,
                        "item_count": item.quantity,
                        "item_amount_sum": line_total,
                    }
                )
            order.items_total = items_total
            order.shipping_amount = get_shipping_amount(items_total)
            order.save(
                update_fields=[
                    "items_total",
                    "shipping_amount",
                    "payable_amount",
                    "updated_at",
                ]
            )
            create_order_audit_log(
                order,
                "order_created",
                actor=request.user,
                note="Order created from checkout.",
                payload={"items_total": order.items_total},
            )
            notify_order_parties(order, "created")
            cart.cart_items.all().delete()  # type: ignore
        try:
            payment_result = ZarinPalClient().request_payment(
                amount=order.payable_amount,
                description=order.description,
                metadata={
                    "mobile": request.user.phone,
                    "email": request.user.email or "",
                    "order_id": order.order_number,
                },
                cart_data={"items": items_payload},
            )
        except ValueError as exc:
            order.payment_status = OrderModel.PaymentStatus.FAILED
            order.status = OrderModel.Status.CANCELLED
            order.save(update_fields=["payment_status", "status", "updated_at"])
            create_order_audit_log(
                order,
                "payment_request_failed",
                actor=request.user,
                note=str(exc),
            )
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except requests.RequestException as exc:
            order.payment_status = OrderModel.PaymentStatus.FAILED
            order.status = OrderModel.Status.CANCELLED
            order.save(update_fields=["payment_status", "status", "updated_at"])
            create_order_audit_log(
                order,
                "payment_request_failed",
                actor=request.user,
                note=str(exc),
            )
            return Response(
                {"detail": f"Payment gateway request failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        if not payment_result.ok:
            order.payment_status = OrderModel.PaymentStatus.FAILED
            order.status = OrderModel.Status.CANCELLED
            order.payment_attempts += 1
            order.save(
                update_fields=[
                    "payment_status",
                    "status",
                    "payment_attempts",
                    "updated_at",
                ]
            )
            create_order_audit_log(
                order,
                "payment_request_rejected",
                actor=request.user,
                note=payment_result.message,
                payload={"code": payment_result.code},
            )
            return Response(
                {
                    "detail": payment_result.message,
                    "code": payment_result.code,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.authority = payment_result.authority
        order.payment_url = payment_result.payment_url
        order.payment_status = OrderModel.PaymentStatus.PENDING_VERIFICATION
        order.payment_attempts += 1
        order.save(
            update_fields=[
                "authority",
                "payment_url",
                "payment_status",
                "payment_attempts",
                "updated_at",
            ]
        )
        create_order_audit_log(
            order,
            "payment_request_created",
            actor=request.user,
            note="Payment request created successfully.",
            payload={"authority": order.authority},
        )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListView(APIView):
    def get(self, request):
        orders = (
            OrderModel.objects.filter(user=request.user, is_deleted=False)
            .prefetch_related("items")
            .order_by("-created_at")
        )
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderDetailView(APIView):
    def get(self, request, order_id):
        try:
            order = (
                OrderModel.objects.filter(user=request.user, is_deleted=False)
                .prefetch_related("items")
                .get(id=order_id)
            )
        except OrderModel.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class OrderPaymentRetryView(APIView):
    def post(self, request, order_id):
        try:
            order = OrderModel.objects.prefetch_related("items").get(
                id=order_id,
                user=request.user,
                is_deleted=False,
            )
        except OrderModel.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if order.payment_status == OrderModel.PaymentStatus.PAID:
            return Response(
                {"detail": "Order is already paid."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        items_payload = [
            {
                "item_name": item.product_name,
                "item_amount": item.unit_price,
                "item_count": item.quantity,
                "item_amount_sum": item.line_total,
            }
            for item in order.items.filter(is_deleted=False)  # type: ignore
        ]
        try:
            payment_result = ZarinPalClient().request_payment(
                amount=order.payable_amount,
                description=order.description
                or f"Payment for order {order.order_number}",
                metadata={
                    "mobile": request.user.phone,
                    "email": request.user.email or "",
                    "order_id": order.order_number,
                },
                cart_data={"items": items_payload},
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except requests.RequestException as exc:
            return Response(
                {"detail": f"Payment gateway request failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        if not payment_result.ok:
            order.payment_status = OrderModel.PaymentStatus.FAILED
            order.status = OrderModel.Status.CANCELLED
            order.payment_attempts += 1
            order.save(
                update_fields=[
                    "payment_status",
                    "status",
                    "payment_attempts",
                    "updated_at",
                ]
            )
            return Response(
                {"detail": payment_result.message, "code": payment_result.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.authority = payment_result.authority
        order.payment_url = payment_result.payment_url
        order.payment_status = OrderModel.PaymentStatus.PENDING_VERIFICATION
        order.status = OrderModel.Status.PENDING
        order.payment_attempts += 1
        order.save(
            update_fields=[
                "authority",
                "payment_url",
                "payment_status",
                "status",
                "payment_attempts",
                "updated_at",
            ]
        )
        create_order_audit_log(
            order,
            "payment_retry_created",
            actor=request.user,
            note="Payment retry request created.",
            payload={"authority": order.authority},
        )
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class ZarinPalVerifyView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        authority = request.query_params.get("Authority")
        callback_status = request.query_params.get("Status")
        if not authority:
            return Response(
                {"detail": "Authority is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            order = OrderModel.objects.prefetch_related("items").get(
                authority=authority,
                is_deleted=False,
            )
        except OrderModel.DoesNotExist:
            return Response(
                {"detail": "Order not found for this authority."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if order.payment_status == OrderModel.PaymentStatus.PAID:
            return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
        order.callback_status = callback_status or ""
        order.save(update_fields=["callback_status", "updated_at"])
        if callback_status != "OK":
            order.payment_status = OrderModel.PaymentStatus.FAILED
            order.status = OrderModel.Status.CANCELLED
            order.save(update_fields=["payment_status", "status", "updated_at"])
            create_order_audit_log(
                order,
                "payment_cancelled",
                note="User cancelled payment in gateway callback.",
            )
            notify_order_parties(order, "cancelled")
            return Response(
                {"detail": "Payment was cancelled or failed by the user."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            verification = ZarinPalClient().verify_payment(
                amount=order.payable_amount,
                authority=authority,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except requests.RequestException as exc:
            return Response(
                {"detail": f"Payment verification failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        if not verification.ok:
            order.payment_status = OrderModel.PaymentStatus.FAILED
            order.status = OrderModel.Status.CANCELLED
            order.save(update_fields=["payment_status", "status", "updated_at"])
            create_order_audit_log(
                order,
                "payment_verification_failed",
                note=verification.message,
                payload={"code": verification.code},
            )
            return Response(
                {"detail": verification.message, "code": verification.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            locked_order = OrderModel.objects.select_for_update().get(id=order.id)  # type: ignore
            if locked_order.payment_status != OrderModel.PaymentStatus.PAID:
                for item in locked_order.items.select_related("product").filter(  # type: ignore
                    is_deleted=False
                ):
                    product = item.product
                    if product is None or product.is_deleted or not product.is_active:
                        locked_order.payment_status = OrderModel.PaymentStatus.FAILED
                        locked_order.status = OrderModel.Status.CANCELLED
                        locked_order.save(
                            update_fields=["payment_status", "status", "updated_at"]
                        )
                        return Response(
                            {
                                "detail": f"Product '{item.product_name}' is no longer available."
                            },
                            status=status.HTTP_409_CONFLICT,
                        )
                    product = (
                        type(product).objects.select_for_update().get(id=product.id)
                    )
                    if product.stock < item.quantity:
                        locked_order.payment_status = OrderModel.PaymentStatus.FAILED
                        locked_order.status = OrderModel.Status.CANCELLED
                        locked_order.save(
                            update_fields=["payment_status", "status", "updated_at"]
                        )
                        return Response(
                            {
                                "detail": f"Insufficient stock for '{item.product_name}' during verification."
                            },
                            status=status.HTTP_409_CONFLICT,
                        )
                    product.stock -= item.quantity
                    product.save(update_fields=["stock", "updated_at"])
                    create_order_audit_log(
                        locked_order,
                        "stock_deducted",
                        note=f"Deducted {item.quantity} from {item.product_name}.",
                        payload={"product_id": product.id, "quantity": item.quantity},
                    )
                locked_order.payment_status = OrderModel.PaymentStatus.PAID
                locked_order.status = OrderModel.Status.PAID
                locked_order.ref_id = verification.ref_id
                locked_order.paid_at = timezone.now()
                locked_order.save(
                    update_fields=[
                        "payment_status",
                        "status",
                        "ref_id",
                        "paid_at",
                        "updated_at",
                    ]
                )
                create_order_audit_log(
                    locked_order,
                    "payment_verified",
                    note="Payment verified successfully.",
                    payload={"ref_id": locked_order.ref_id},
                )
                order = locked_order
        notify_order_parties(order, "paid")
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class SellerOrderListView(APIView):
    def get(self, request):
        if not request.user.is_seller:
            return Response(
                {"detail": "Only sellers can access seller orders."},
                status=status.HTTP_403_FORBIDDEN,
            )
        orders = get_seller_order_queryset(request.user).order_by("-created_at")
        serializer = SellerOrderSerializer(
            orders,
            many=True,
            context={"seller": request.user},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class SellerOrderDetailView(APIView):
    def get(self, request, order_id):
        if not request.user.is_seller:
            return Response(
                {"detail": "Only sellers can access seller orders."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            order = get_seller_order_queryset(request.user).get(id=order_id)
        except OrderModel.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = SellerOrderSerializer(order, context={"seller": request.user})
        return Response(serializer.data, status=status.HTTP_200_OK)


class SellerOrderStatusUpdateView(APIView):
    def patch(self, request, order_id):
        if not request.user.is_seller:
            return Response(
                {"detail": "Only sellers can manage order statuses."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = SellerOrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        next_status = serializer.validated_data["status"]  # type: ignore
        try:
            order = get_seller_order_queryset(request.user).get(id=order_id)
        except OrderModel.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if order.payment_status != OrderModel.PaymentStatus.PAID:
            return Response(
                {"detail": "Only paid orders can move through the seller lifecycle."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not can_transition_order_status(order, next_status):
            return Response(
                {
                    "detail": (
                        f"Order cannot transition from {order.status} to {next_status}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = next_status
        order.save(update_fields=["status", "updated_at"])
        create_order_audit_log(
            order,
            "seller_status_updated",
            actor=request.user,
            note=f"Seller changed status to {next_status}.",
        )
        notify_order_parties(order, next_status)
        response_serializer = SellerOrderSerializer(
            order,
            context={"seller": request.user},
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class OrderAuditLogView(APIView):
    def get(self, request, order_id):
        try:
            order = OrderModel.objects.get(
                id=order_id,
                user=request.user,
                is_deleted=False,
            )
        except OrderModel.DoesNotExist:
            if request.user.is_seller:
                try:
                    order = get_seller_order_queryset(request.user).get(id=order_id)
                except OrderModel.DoesNotExist:
                    return Response(
                        {"detail": "Order not found."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                return Response(
                    {"detail": "Order not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        serializer = OrderAuditLogSerializer(order.audit_logs.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


