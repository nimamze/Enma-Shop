from rest_framework import serializers
from Shops.models import ShopModel, ShopImageModel, ShopVideoModel
from Core.utils.phone_number_validate import validate_iranian_phone


class ShopImageSerializer(serializers.ModelSerializer):
    def validate_image(self, value):
        content_type = getattr(value, "content_type", "")
        if not content_type.startswith("image/"):
            raise serializers.ValidationError("Only image files are allowed.")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Image size must be 5 MB or less.")
        return value

    class Meta:
        model = ShopImageModel
        fields = ["id", "image", "order"]
        read_only_fields = ["id"]


class ShopVideoSerializer(serializers.ModelSerializer):
    def validate_video(self, value):
        content_type = getattr(value, "content_type", "")
        if not content_type.startswith("video/"):
            raise serializers.ValidationError("Only video files are allowed.")
        if value.size > 100 * 1024 * 1024:
            raise serializers.ValidationError("Video size must be 100 MB or less.")
        return value

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
        read_only_fields = [
            "id",
            "user",
            "rating",
            "images",
            "videos",
            "is_deleted",
            "created_at",
            "updated_at",
        ]

    def validate_phone(self, value):
        phone = value.strip()
        validate_iranian_phone(phone)
        return phone
