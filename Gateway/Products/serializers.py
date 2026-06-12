from rest_framework import serializers
from Products.models import (
    CategoryModel,
    ProductModel,
    ProductImageModel,
    ProductVideoModel,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryModel
        fields = ["id", "name", "parent", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductImageSerializer(serializers.ModelSerializer):
    def validate_image(self, value):
        content_type = getattr(value, "content_type", "")
        if not content_type.startswith("image/"):
            raise serializers.ValidationError("Only image files are allowed.")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Image size must be 5 MB or less.")
        return value

    class Meta:
        model = ProductImageModel
        fields = ["id", "image", "order", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductVideoSerializer(serializers.ModelSerializer):
    def validate_video(self, value):
        content_type = getattr(value, "content_type", "")
        if not content_type.startswith("video/"):
            raise serializers.ValidationError("Only video files are allowed.")
        if value.size > 100 * 1024 * 1024:
            raise serializers.ValidationError("Video size must be 100 MB or less.")
        return value

    class Meta:
        model = ProductVideoModel
        fields = ["id", "video", "order", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    videos = ProductVideoSerializer(many=True, read_only=True)
    shop_name = serializers.CharField(source="shop.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = ProductModel
        fields = [
            "id",
            "shop",
            "shop_name",
            "category",
            "category_name",
            "name",
            "description",
            "price",
            "stock",
            "is_active",
            "images",
            "videos",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "shop",
            "shop_name",
            "category_name",
            "images",
            "videos",
            "created_at",
            "updated_at",
        ]
