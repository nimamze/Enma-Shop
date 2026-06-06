from django.contrib import admin
from Products.models import (
    CategoryModel,
    ProductModel,
    ProductImageModel,
    ProductVideoModel,
)


@admin.register(CategoryModel)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "is_deleted")
    list_filter = ("is_deleted", "parent")
    search_fields = ("name",)
    readonly_fields = ("id",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)


class ProductImageInline(admin.TabularInline):
    model = ProductImageModel
    extra = 1
    fields = ("image", "order", "is_deleted")
    readonly_fields = ("is_deleted",)


class ProductVideoInline(admin.TabularInline):
    model = ProductVideoModel
    extra = 1
    fields = ("video", "order", "is_deleted")
    readonly_fields = ("is_deleted",)


@admin.register(ProductModel)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "shop",
        "category",
        "price",
        "stock",
        "is_active",
        "is_deleted",
    )
    list_filter = ("is_deleted", "is_active", "shop", "category")
    search_fields = ("name", "description", "shop__name", "category__name")
    readonly_fields = ("id",)
    list_editable = ("price", "stock", "is_active")
    inlines = [
        ProductImageInline,
        ProductVideoInline,
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)


@admin.register(ProductImageModel)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "image", "order", "is_deleted")
    list_filter = ("is_deleted", "product")
    search_fields = ("product__name",)
    readonly_fields = ("id",)
    list_editable = ("order",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)


@admin.register(ProductVideoModel)
class ProductVideoAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "video", "order", "is_deleted")
    list_filter = ("is_deleted", "product")
    search_fields = ("product__name",)
    readonly_fields = ("id",)
    list_editable = ("order",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)
