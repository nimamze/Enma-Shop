from rest_framework import serializers
from Addresses.models import Address
from Orders.models import CartItemModel, CartModel, OrderItemModel, OrderModel
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
    class Meta:
        model = OrderItemModel
        fields = [
            "id",
            "product",
            "shop",
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
