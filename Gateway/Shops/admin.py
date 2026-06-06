from django.contrib import admin
from Shops.models import ShopModel


@admin.register(ShopModel)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "phone", "email", "rating", "is_deleted")
    list_filter = ("is_deleted", "rating", "user")
    search_fields = ("name", "user__username", "phone", "email")
    readonly_fields = ("id", "user", "rating")
    list_editable = ("rating",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False)
