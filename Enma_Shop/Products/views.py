from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from elasticsearch import ConnectionError as ElasticsearchConnectionError, TransportError
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
from Core.utils.elasticsearch.client import es
from Core.utils.elasticsearch.indexes import PRODUCTS_INDEX


class CategoryView(APIView):
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return super().get_permissions()
        return [IsAdminUser()]

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
        with transaction.atomic():
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
        with transaction.atomic():
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
                product = (
                    ProductModel.objects.filter(
                        id=id,
                        shop__user=user,
                        shop__is_deleted=False,
                        is_deleted=False,
                    )
                    .select_related("shop", "category")
                    .prefetch_related("images", "videos")
                    .get()
                )
            except ProductModel.DoesNotExist:
                return Response(
                    {"detail": "Product not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = self.serializer_class(product)
            return Response(serializer.data, status=status.HTTP_200_OK)
        products = (
            ProductModel.objects.filter(
                shop__user=user, shop__is_deleted=False, is_deleted=False
            )
            .select_related("shop", "category")
            .prefetch_related("images", "videos")
        )
        serializer = self.serializer_class(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        if not user.is_seller:
            return Response(
                {"detail": "Only sellers can create products."},
                status=status.HTTP_403_FORBIDDEN,
            )
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
        with transaction.atomic():
            serializer.save(shop=shop)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, id):
        user = request.user
        try:
            product = ProductModel.objects.get(
                id=id,
                shop__user=user,
                shop__is_deleted=False,
                is_deleted=False,
            )
        except ProductModel.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        user = request.user
        try:
            product = ProductModel.objects.get(
                id=id,
                shop__user=user,
                shop__is_deleted=False,
                is_deleted=False,
            )
        except ProductModel.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicProductView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer

    def get(self, request, id=None):
        queryset = (
            ProductModel.objects.filter(
                is_deleted=False,
                is_active=True,
                shop__is_deleted=False,
            )
            .select_related("shop", "category")
            .prefetch_related("images", "videos")
        )
        if id:
            try:
                product = queryset.get(id=id)
            except ProductModel.DoesNotExist:
                return Response(
                    {"detail": "Product not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = self.serializer_class(product)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductImageView(APIView):
    serializer_class = ProductImageSerializer

    def post(self, request, product_id):
        user = request.user
        try:
            product = ProductModel.objects.get(
                id=product_id,
                shop__user=user,
                shop__is_deleted=False,
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
                shop__is_deleted=False,
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


class ProductSearchView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @staticmethod
    def parse_int_param(value, default=None, minimum=None, maximum=None):
        if value in (None, ""):
            return default
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid integer parameter.") from exc
        if minimum is not None and parsed < minimum:
            parsed = minimum
        if maximum is not None and parsed > maximum:
            parsed = maximum
        return parsed

    def get(self, request):
        q = request.query_params.get("q")
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        category_id = request.query_params.get("category")
        shop_id = request.query_params.get("shop")
        in_stock = request.query_params.get("in_stock")
        try:
            page = self.parse_int_param(
                request.query_params.get("page", 1), default=1, minimum=1
            )
            page_size = self.parse_int_param(
                request.query_params.get("page_size", 20),
                default=20,
                minimum=1,
                maximum=100,
            )
            min_price_value = self.parse_int_param(min_price)
            max_price_value = self.parse_int_param(max_price)
            category_id_value = self.parse_int_param(category_id)
            shop_id_value = self.parse_int_param(shop_id)
        except ValueError:
            return Response(
                {"detail": "Invalid numeric query parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        must = []
        filters = [
            {"term": {"is_active": True}},
        ]
        if q:
            must.append(
                {
                    "multi_match": {
                        "query": q,
                        "fields": [
                            "name^3",
                            "description",
                            "shop_name",
                            "category_name",
                        ],
                        "fuzziness": "AUTO",
                    }
                }
            )
        else:
            must.append({"match_all": {}})
        price_range = {}
        if min_price_value is not None:
            price_range["gte"] = min_price_value
        if max_price_value is not None:
            price_range["lte"] = max_price_value
        if price_range:
            filters.append({"range": {"price": price_range}})  # type: ignore
        if category_id_value is not None:
            filters.append({"term": {"category_id": category_id_value}})  # type: ignore
        if shop_id_value is not None:
            filters.append({"term": {"shop_id": shop_id_value}})  # type: ignore
        if in_stock == "true":
            filters.append({"range": {"stock": {"gt": 0}}})  # type: ignore
        query = {"bool": {"must": must, "filter": filters}}
        from_ = (page - 1) * page_size # type: ignore
        try:
            result = es.search(
                index=PRODUCTS_INDEX,
                query=query,
                from_=from_,
                size=page_size,
                sort=[
                    {"_score": {"order": "desc"}},
                    {"created_at": {"order": "desc"}},
                ],
            )
        except (ElasticsearchConnectionError, TransportError):
            return Response(
                {"detail": "Search service is temporarily unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        hits = result["hits"]["hits"]
        total = result["hits"]["total"]["value"]
        data = {
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": [
                {
                    **hit["_source"],
                    "score": hit["_score"],
                }
                for hit in hits
            ],
        }
        return Response(data, status=status.HTTP_200_OK)
