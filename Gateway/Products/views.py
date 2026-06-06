from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from Shops.models import ShopModel
from Products.models import (
    CategoryModel,
    ProductModel,
    ProductImageModel,
    ProductVideoModel,
)
from Products.serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductImageSerializer,
    ProductVideoSerializer,
)


class CategoryView(APIView):
    serializer_class = CategorySerializer

    def get(self, request, id=None):
        if id:
            try:
                category = CategoryModel.objects.get(id=id, is_deleted=False)
            except CategoryModel.DoesNotExist:
                return Response(
                    {"detail": "Category not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = self.serializer_class(category)
            return Response(serializer.data, status=status.HTTP_200_OK)
        categories = CategoryModel.objects.filter(is_deleted=False)
        serializer = self.serializer_class(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, id):
        try:
            category = CategoryModel.objects.get(id=id, is_deleted=False)
        except CategoryModel.DoesNotExist:
            return Response(
                {"detail": "Category not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        try:
            category = CategoryModel.objects.get(id=id, is_deleted=False)
        except CategoryModel.DoesNotExist:
            return Response(
                {"detail": "Category not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductView(APIView):
    serializer_class = ProductSerializer

    def get(self, request, id=None):
        user = request.user
        if id:
            try:
                product = ProductModel.objects.get(
                    id=id,
                    shop__user=user,
                    is_deleted=False,
                )
            except ProductModel.DoesNotExist:
                return Response(
                    {"detail": "Product not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = self.serializer_class(product)
            return Response(serializer.data, status=status.HTTP_200_OK)
        products = (
            ProductModel.objects.filter(shop__user=user, is_deleted=False)
            .select_related("shop", "category")
            .prefetch_related("images", "videos")
        )
        serializer = self.serializer_class(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        shop_id = request.data.get("shop")
        if not shop_id:
            return Response(
                {"shop": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            shop = ShopModel.objects.get(
                id=shop_id,
                user=user,
                is_deleted=False,
            )
        except ShopModel.DoesNotExist:
            return Response(
                {"detail": "Shop not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(shop=shop)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, id):
        user = request.user
        try:
            product = ProductModel.objects.get(
                id=id,
                shop__user=user,
                is_deleted=False,
            )
        except ProductModel.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        user = request.user
        try:
            product = ProductModel.objects.get(
                id=id,
                shop__user=user,
                is_deleted=False,
            )
        except ProductModel.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductImageView(APIView):
    serializer_class = ProductImageSerializer

    def post(self, request, product_id):
        user = request.user
        try:
            product = ProductModel.objects.get(
                id=product_id,
                shop__user=user,
                is_deleted=False,
            )
        except ProductModel.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, product_id, image_id):
        user = request.user
        try:
            product_image = ProductImageModel.objects.get(
                id=image_id,
                product_id=product_id,
                product__shop__user=user,
                is_deleted=False,
            )
        except ProductImageModel.DoesNotExist:
            return Response(
                {"detail": "Product image not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        product_image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductVideoView(APIView):
    serializer_class = ProductVideoSerializer

    def post(self, request, product_id):
        user = request.user
        try:
            product = ProductModel.objects.get(
                id=product_id,
                shop__user=user,
                is_deleted=False,
            )
        except ProductModel.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, product_id, video_id):
        user = request.user
        try:
            product_video = ProductVideoModel.objects.get(
                id=video_id,
                product_id=product_id,
                product__shop__user=user,
                is_deleted=False,
            )
        except ProductVideoModel.DoesNotExist:
            return Response(
                {"detail": "Product video not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        product_video.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
