from django.contrib import admin
from Addresses.models import AddressUser


@admin.register(AddressUser)
class AddressUserAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "title",
        "province",
        "city",
        "street",
        "plaque",
        "is_default",
    )
    list_filter = "is_default"
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
    ordering = ("-province",)
    fieldsets = (
        (
            "User",
            {
                "fields": (
                    "user",
                    "title",
                    "is_default",
                )
            },
        ),
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
