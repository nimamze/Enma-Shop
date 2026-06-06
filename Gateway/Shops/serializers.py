from rest_framework import serializers
from django.contrib.auth import get_user_model
from Shops.models import ShopModel, ShopImageModel, ShopVideoModel
from Core.utils.phone_number_validate import validate_iranian_phone

User = get_user_model()


class ShopImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopImageModel
        fields = ["id", "image", "order"]
        read_only_fields = ["id"]


class ShopVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopVideoModel
        fields = ["id", "video", "order"]
        read_only_fields = ["id"]


class ShopSerializer(serializers.ModelSerializer):
    images = ShopImageSerializer(many=True, read_only=True)
    videos = ShopVideoSerializer(many=True, read_only=True)

    class Meta:
        model = ShopModel
        fields = "__all__"
        read_only_fields = ["id", "user", "rating", "images", "videos"]

    def validate_phone(self, value):
        phone = value.strip()
        validate_iranian_phone(phone)
        return phone
