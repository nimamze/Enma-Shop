from django.contrib import admin
from Addresses.models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "user_phone",
        "title",
        "province",
        "city",
        "street",
        "number",
        "is_default",
    )
    list_filter = ("is_default",)
    search_fields = (
        "user__phone",
        "user__first_name",
        "user__last_name",
        "province",
        "city",
        "street",
        "number",
        "postal_code",
    )
    ordering = ("-created_at",)
    list_editable = ("is_default",)
    fieldsets = (
        ("User", {"fields": ("user", "title", "is_default")}),
        (
            "Location",
            {
                "fields": (
                    "latitude",
                    "longitude",
                    "province",
                    "city",
                    "street",
                    "alley",
                    "number",
                    "unit",
                    "postal_code",
                )
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="User Phone")
    def user_phone(self, obj):
        return obj.user.phone
