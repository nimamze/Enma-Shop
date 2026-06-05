from django.contrib import admin
from Addresses.models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "user__phone",
        "title",
        "province",
        "city",
        "street",
        "plaque",
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
        "plaque",
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
                    "neighbourhood",
                    "street",
                    "alley",
                    "plaque",
                    "unit",
                    "postal_code",
                )
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")
