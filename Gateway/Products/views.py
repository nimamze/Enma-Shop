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
from Core.utils.elasticsearch.client import es
from Core.utils.elasticsearch.indexes import PRODUCTS_INDEX


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


class ProductSearchView(APIView):
    def get(self, request):
        q = request.query_params.get("q")
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        category_id = request.query_params.get("category")
        shop_id = request.query_params.get("shop")
        in_stock = request.query_params.get("in_stock")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > 100:
            page_size = 100
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
        if min_price:
            price_range["gte"] = int(min_price)
        if max_price:
            price_range["lte"] = int(max_price)
        if price_range:
            filters.append({"range": {"price": price_range}}) # type: ignore
        if category_id:
            filters.append({"term": {"category_id": int(category_id)}}) # type: ignore
        if shop_id:
            filters.append({"term": {"shop_id": int(shop_id)}}) # type: ignore
        if in_stock == "true":
            filters.append({"range": {"stock": {"gt": 0}}}) # type: ignore
        query = {"bool": {"must": must, "filter": filters}}
        from_ = (page - 1) * page_size
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
