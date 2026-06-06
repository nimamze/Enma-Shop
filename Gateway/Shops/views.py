from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from Shops.serializers import ShopSerializer
from Shops.models import ShopModel
from django.contrib.auth import get_user_model

User = get_user_model()


class ShopView(APIView):
    serializer_class = ShopSerializer

    def get(self, request, id=None):
        user = request.user
        if id:
            try:
                shop = ShopModel.objects.get(id=id, user=user, is_deleted=False)
                serializer = self.serializer_class(shop)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ShopModel.DoesNotExist:
                return Response(
                    {"detail": "Shop not found."}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            shops = ShopModel.objects.filter(user=user, is_deleted=False)
            serializer = self.serializer_class(shops, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, id):
        user = request.user
        try:
            shop = ShopModel.objects.get(id=id, user=user, is_deleted=False)
        except ShopModel.DoesNotExist:
            return Response(
                {"detail": "Shop not found."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.serializer_class(shop, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        user = request.user
        try:
            shop = ShopModel.objects.get(id=id, user=user, is_deleted=False)
        except ShopModel.DoesNotExist:
            return Response(
                {"detail": "Shop not found."}, status=status.HTTP_404_NOT_FOUND
            )
        shop.is_deleted = True
        shop.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
