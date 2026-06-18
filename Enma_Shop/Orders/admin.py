from django.contrib import admin
from Orders.models import CartItemModel, CartModel, OrderItemModel, OrderModel


class CartItemInline(admin.TabularInline):
    model = CartItemModel
    extra = 0


@admin.register(CartModel)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "updated_at")
    search_fields = ("user__phone",)
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItemModel
    extra = 0
    readonly_fields = (
        "product",
        "shop",
        "product_name",
        "shop_name",
        "quantity",
        "unit_price",
        "line_total",
    )


@admin.register(OrderModel)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_number",
        "user",
        "status",
        "payment_status",
        "payable_amount",
        "ref_id",
        "created_at",
    )
    search_fields = ("order_number", "user__phone", "authority", "ref_id")
    list_filter = ("status", "payment_status", "created_at")
    readonly_fields = (
        "order_number",
        "authority",
        "ref_id",
        "payment_url",
        "payment_attempts",
        "paid_at",
        "created_at",
        "updated_at",
    )
    inlines = [OrderItemInline]
