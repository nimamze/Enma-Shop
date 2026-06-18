import requests
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from Orders.models import CartItemModel, CartModel, OrderItemModel, OrderModel
from Orders.payment import ZarinPalClient
from Orders.serializers import (
    CartItemSerializer,
    CartItemUpdateSerializer,
    CartItemWriteSerializer,
    CartSerializer,
    CheckoutSerializer,
    OrderSerializer,
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
        with transaction.atomic():
            cart_item = CartItemModel.objects.filter(cart=cart, product=product).first()
            created = cart_item is None
            if created:
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
            order.payable_amount = (
                order.items_total + order.shipping_amount - order.discount_amount
            )
            order.save(update_fields=["items_total", "payable_amount", "updated_at"])
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
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except requests.RequestException as exc:
            order.payment_status = OrderModel.PaymentStatus.FAILED
            order.status = OrderModel.Status.CANCELLED
            order.save(update_fields=["payment_status", "status", "updated_at"])
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
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListView(APIView):
    def get(self, request):
        orders = OrderModel.objects.filter(user=request.user).prefetch_related("items")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderDetailView(APIView):
    def get(self, request, order_id):
        try:
            order = (
                OrderModel.objects.filter(user=request.user)
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
                order = locked_order
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
