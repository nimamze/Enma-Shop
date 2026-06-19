from django.contrib import admin

from Orders.models import (
    CartItemModel,
    CartModel,
    OrderAuditLogModel,
    OrderItemModel,
    OrderModel,
)


class CartItemInline(admin.TabularInline):
    model = CartItemModel
    extra = 0


@admin.register(CartItemModel)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity", "created_at", "updated_at")
    search_fields = ("cart__user__phone", "product__name")
    list_filter = ("created_at", "updated_at")


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


class OrderAuditLogInline(admin.TabularInline):
    model = OrderAuditLogModel
    extra = 0
    can_delete = False
    readonly_fields = ("actor", "action", "note", "payload", "created_at")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(OrderItemModel)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "product_name",
        "shop_name",
        "quantity",
        "unit_price",
        "line_total",
        "created_at",
    )
    search_fields = (
        "order__order_number",
        "product_name",
        "shop_name",
        "product__name",
        "shop__name",
    )
    list_filter = ("created_at", "updated_at")
    readonly_fields = ("line_total", "created_at", "updated_at")


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
    inlines = [OrderItemInline, OrderAuditLogInline]


@admin.register(OrderAuditLogModel)
class OrderAuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "actor", "action", "created_at")
    search_fields = ("order__order_number", "actor__phone", "action", "note")
    list_filter = ("action", "created_at")
    readonly_fields = ("order", "actor", "action", "note", "payload", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
