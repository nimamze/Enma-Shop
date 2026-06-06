from celery import shared_task
from elasticsearch import NotFoundError
from Core.utils.elasticsearch.client import es
from Core.utils.elasticsearch.indexes import PRODUCTS_INDEX
from Products.models import ProductModel


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def index_product_to_elastic(self, product_id):

    try:
        product = (
            ProductModel.objects.select_related("shop", "category")
            .prefetch_related("images")
            .get(id=product_id, is_deleted=False)
        )
    except ProductModel.DoesNotExist:
        delete_product_from_elastic.delay(product_id)  # type: ignore
        return
    if not product.is_active:
        delete_product_from_elastic.delay(product_id)  # type: ignore
        return
    thumbnail = None
    first_image = (
        product.images.filter(is_deleted=False).order_by("order", "id").first()  # type: ignore
    )
    if first_image and first_image.image:
        try:
            thumbnail = first_image.image.url
        except ValueError:
            thumbnail = None
    document = {
        "id": product.id,  # type: ignore
        "name": product.name,
        "description": product.description or "",
        "price": int(product.price),
        "stock": product.stock,
        "is_active": product.is_active,
        "shop_id": product.shop_id,  # type: ignore
        "shop_name": product.shop.name,
        "category_id": product.category_id,  # type: ignore
        "category_name": product.category.name if product.category else None,
        "thumbnail": thumbnail,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat(),
    }
    es.index(
        index=PRODUCTS_INDEX,
        id=product.id,  # type: ignore
        document=document,
    )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def delete_product_from_elastic(self, product_id):
    try:
        es.delete(
            index=PRODUCTS_INDEX,
            id=product_id,
        )
    except NotFoundError:
        pass
