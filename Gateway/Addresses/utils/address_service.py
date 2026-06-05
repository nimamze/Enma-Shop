from django.db import transaction
from django.conf import settings
from rest_framework.exceptions import ValidationError
from Addresses.models import Address


class AddressService:
    @staticmethod
    def create_address(*, user, validated_data):
        limit = getattr(settings, "USER_ADDRESS_LIMIT", 3)
        if Address.objects.filter(user=user).count() >= limit:
            raise ValidationError(f"Maximum {limit} addresses allowed per user.")
        is_default = validated_data.get("is_default", False)
        with transaction.atomic():
            if is_default:
                Address.objects.filter(user=user, is_default=True).update(
                    is_default=False
                )
            return Address.objects.create(user=user, **validated_data)

    @staticmethod
    def update_address(*, instance, validated_data):
        user = instance.user
        is_default = validated_data.get("is_default", None)
        with transaction.atomic():
            if is_default is True:
                Address.objects.filter(user=user, is_default=True).exclude(
                    pk=instance.pk
                ).update(is_default=False)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
