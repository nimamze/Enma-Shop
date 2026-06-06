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
    class Meta:
        model = ProductImageModel
        fields = ["id", "image", "order", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductVideoSerializer(serializers.ModelSerializer):
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
