from django.contrib import admin
from Shops.models import ShopModel, ShopImageModel, ShopVideoModel


class ShopImageInline(admin.TabularInline):
    model = ShopImageModel
    extra = 1
    fields = ("image", "order", "is_deleted")
    readonly_fields = ("is_deleted",)


class ShopVideoInline(admin.TabularInline):
    model = ShopVideoModel
    extra = 1
    fields = ("video", "order", "is_deleted")
    readonly_fields = ("is_deleted",)


@admin.register(ShopModel)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "phone", "email", "rating", "is_deleted")
    list_filter = ("is_deleted", "rating", "user")
    search_fields = ("name", "user__phone", "phone", "email")
    readonly_fields = ("id", "user")
    list_editable = ("rating",)
    inlines = [ShopImageInline, ShopVideoInline]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)


@admin.register(ShopImageModel)
class ShopImageAdmin(admin.ModelAdmin):
    list_display = ("id", "shop", "image", "order", "is_deleted")
    list_filter = ("is_deleted", "shop")
    search_fields = ("shop__name",)
    list_editable = ("order",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)


@admin.register(ShopVideoModel)
class ShopVideoAdmin(admin.ModelAdmin):
    list_display = ("id", "shop", "video", "order", "is_deleted")
    list_filter = ("is_deleted", "shop")
    search_fields = ("shop__name",)
    list_editable = ("order",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)
