from rest_framework import serializers
from Addresses.models import Address
from Orders.models import (
    CartItemModel,
    CartModel,
    OrderAuditLogModel,
    OrderItemModel,
    OrderModel,
)
from Products.models import ProductModel


class CartItemWriteSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        try:
            product = ProductModel.objects.select_related("shop", "category").get(
                id=value,
                is_deleted=False,
                is_active=True,
                shop__is_deleted=False,
            )
        except ProductModel.DoesNotExist as exc:
            raise serializers.ValidationError("Product not found.") from exc
        if product.stock <= 0:
            raise serializers.ValidationError("Product is out of stock.")
        self.context["product"] = product
        return value

    def validate(self, attrs):
        product = self.context["product"]
        quantity = attrs["quantity"]
        if product.stock < quantity:
            raise serializers.ValidationError(
                {"quantity": "Requested quantity exceeds available stock."}
            )
        return attrs


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class SellerOrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            OrderModel.Status.PROCESSING,
            OrderModel.Status.SHIPPED,
            OrderModel.Status.DELIVERED,
            OrderModel.Status.CANCELLED,
        ]
    )


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source="product.id", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    shop_id = serializers.IntegerField(source="product.shop.id", read_only=True)
    shop_name = serializers.CharField(source="product.shop.name", read_only=True)
    unit_price = serializers.IntegerField(source="product.price", read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItemModel
        fields = [
            "id",
            "product_id",
            "product_name",
            "shop_id",
            "shop_name",
            "quantity",
            "unit_price",
            "subtotal",
        ]
        read_only_fields = fields

    def get_subtotal(self, obj):
        return obj.quantity * obj.product.price


class CartSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = CartModel
        fields = ["id", "items", "total_amount", "created_at", "updated_at"]
        read_only_fields = fields

    def get_items(self, obj):
        items = obj.cart_items.filter(
            product__is_deleted=False,
            product__shop__is_deleted=False,
        ).select_related("product", "product__shop")
        return CartItemSerializer(items, many=True).data

    def get_total_amount(self, obj):
        total = 0
        items = obj.cart_items.filter(
            product__is_deleted=False,
            product__shop__is_deleted=False,
        ).select_related("product")
        for item in items:
            total += item.quantity * item.product.price
        return total


class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.IntegerField()

    def validate_address_id(self, value):
        user = self.context["request"].user
        try:
            address = Address.objects.get(id=value, user=user, is_deleted=False)
        except Address.DoesNotExist as exc:
            raise serializers.ValidationError("Address not found.") from exc
        self.context["address"] = address
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    shop_id = serializers.IntegerField(source="shop.id", read_only=True)

    class Meta:
        model = OrderItemModel
        fields = [
            "id",
            "product",
            "shop",
            "shop_id",
            "product_name",
            "shop_name",
            "quantity",
            "unit_price",
            "line_total",
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_amount = serializers.IntegerField(source="payable_amount", read_only=True)

    class Meta:
        model = OrderModel
        fields = [
            "id",
            "order_number",
            "address",
            "receiver_name",
            "receiver_phone",
            "address_title",
            "province",
            "city",
            "street",
            "alley",
            "number",
            "unit",
            "postal_code",
            "full_address",
            "status",
            "payment_status",
            "items_total",
            "shipping_amount",
            "discount_amount",
            "payable_amount",
            "total_amount",
            "authority",
            "ref_id",
            "payment_url",
            "description",
            "callback_status",
            "payment_attempts",
            "paid_at",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class SellerOrderSerializer(OrderSerializer):
    customer_phone = serializers.CharField(source="user.phone", read_only=True)
    customer_name = serializers.SerializerMethodField()
    shop = serializers.SerializerMethodField()

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + [
            "customer_phone",
            "customer_name",
            "shop",
        ]

    def get_customer_name(self, obj):
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return full_name or obj.user.phone

    def get_shop(self, obj):
        seller = self.context.get("seller")
        items = obj.items.filter(is_deleted=False).select_related("shop")
        if seller is not None:
            items = items.filter(shop__user=seller)
        first_item = items.first()
        if not first_item or not first_item.shop:
            return None
        shop = first_item.shop
        return {
            "id": shop.id,
            "name": shop.name,
        }


class OrderAuditLogSerializer(serializers.ModelSerializer):
    actor_phone = serializers.CharField(source="actor.phone", read_only=True, allow_null=True)

    class Meta:
        model = OrderAuditLogModel
        fields = [
            "id",
            "actor_phone",
            "action",
            "note",
            "payload",
            "created_at",
        ]
        read_only_fields = fields
