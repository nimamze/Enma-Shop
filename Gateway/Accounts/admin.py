from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from Accounts.models import UserModel
from Accounts.utils.forms import CustomUserCreationForm, CustomUserChangeForm


@admin.register(UserModel)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = UserModel
    list_display = (
        "phone",
        "get_user_fullname",
        "is_seller",
        "is_superuser",
        "is_deleted",
    )
    list_filter = ("is_superuser", "is_seller", "is_deleted", "is_staff", "is_active")
    search_fields = ("phone", "email", "first_name", "last_name")
    ordering = ("phone",)
    readonly_fields = ("created_at", "updated_at", "last_login", "date_joined")

    add_fieldsets = (
        ("Personal Info", {"fields": ("phone", "email", "password1", "password2")}),
        (
            "Permissions",
            {"fields": ("is_seller", "is_staff", "is_active", "is_superuser")},
        ),
    )

    fieldsets = (
        (
            "Personal Info",
            {
                "fields": (
                    "phone",
                    "email",
                    "password",
                    "first_name",
                    "last_name",
                    "image",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_seller",
                    "is_staff",
                    "is_active",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Dates",
            {"fields": ("last_login", "date_joined", "created_at", "updated_at")},
        ),
        ("Soft Delete", {"fields": ("is_deleted",)}),
    )

    @admin.display(description="Full Name")
    def get_user_fullname(self, obj):
        return obj.get_full_name()
