from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from Shops.serializers import (
    ShopImageSerializer,
    ShopSerializer,
    ShopVideoSerializer,
)
from Shops.models import ShopImageModel, ShopModel, ShopVideoModel


class ShopView(APIView):
    serializer_class = ShopSerializer

    def get(self, request, id=None):
        user = request.user
        if id:
            try:
                shop = (
                    ShopModel.objects.filter(id=id, user=user, is_deleted=False)
                    .prefetch_related("images", "videos")
                    .get()
                )
            except ShopModel.DoesNotExist:
                return Response(
                    {"detail": "Shop not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = self.serializer_class(shop)
            return Response(serializer.data, status=status.HTTP_200_OK)
        shops = ShopModel.objects.filter(user=user, is_deleted=False).prefetch_related(
            "images", "videos"
        )
        serializer = self.serializer_class(shops, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        if not user.is_seller:
            return Response(
                {"detail": "Only sellers can create shops."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save(user=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, id):
        user = request.user
        try:
            shop = ShopModel.objects.get(id=id, user=user, is_deleted=False)
        except ShopModel.DoesNotExist:
            return Response(
                {"detail": "Shop not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(shop, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        user = request.user
        try:
            shop = ShopModel.objects.get(id=id, user=user, is_deleted=False)
        except ShopModel.DoesNotExist:
            return Response(
                {"detail": "Shop not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        shop.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicShopView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = ShopSerializer

    def get(self, request, id=None):
        queryset = ShopModel.objects.filter(is_deleted=False).prefetch_related(
            "images", "videos"
        )
        if id:
            try:
                shop = queryset.get(id=id)
            except ShopModel.DoesNotExist:
                return Response(
                    {"detail": "Shop not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = self.serializer_class(shop)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ShopImageView(APIView):
    serializer_class = ShopImageSerializer

    def post(self, request, shop_id):
        user = request.user
        try:
            shop = ShopModel.objects.get(id=shop_id, user=user, is_deleted=False)
        except ShopModel.DoesNotExist:
            return Response(
                {"detail": "Shop not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(shop=shop)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, shop_id, image_id):
        user = request.user
        try:
            shop_image = ShopImageModel.objects.get(
                id=image_id,
                shop_id=shop_id,
                shop__user=user,
                is_deleted=False,
            )
        except ShopImageModel.DoesNotExist:
            return Response(
                {"detail": "Shop image not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        shop_image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShopVideoView(APIView):
    serializer_class = ShopVideoSerializer

    def post(self, request, shop_id):
        user = request.user
        try:
            shop = ShopModel.objects.get(id=shop_id, user=user, is_deleted=False)
        except ShopModel.DoesNotExist:
            return Response(
                {"detail": "Shop not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(shop=shop)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, shop_id, video_id):
        user = request.user
        try:
            shop_video = ShopVideoModel.objects.get(
                id=video_id,
                shop_id=shop_id,
                shop__user=user,
                is_deleted=False,
            )
        except ShopVideoModel.DoesNotExist:
            return Response(
                {"detail": "Shop video not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        shop_video.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
