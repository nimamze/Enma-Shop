from rest_framework import serializers
from django.contrib.auth import get_user_model
from Shops.models import ShopModel
from Core.utils.phone_number_validate import validate_iranian_phone

User = get_user_model()


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopModel
        fields = "__all__"
        read_only_fields = ["id", "user", "rating"]

    def validate_phone(self, value):
        phone = value.strip()
        validate_iranian_phone(phone)
        return phone
