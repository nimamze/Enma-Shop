import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from Shops.models import ShopModel
from Products.models import (
    CategoryModel,
    ProductModel,
    ProductImageModel,
    ProductVideoModel,
)
from Products.tasks import (
    index_product_to_elastic,
    delete_product_from_elastic,
)

logger = logging.getLogger(__name__)


def dispatch_task_safely(task, *args):
    try:
        task.delay(*args)  # type: ignore
    except Exception:
        logger.exception("Failed to dispatch task %s with args=%s", task.name, args)


def reindex_products(queryset):
    product_ids = queryset.values_list("id", flat=True)

    def run_task():
        for product_id in product_ids.iterator():
            dispatch_task_safely(index_product_to_elastic, product_id)

    transaction.on_commit(run_task)


@receiver(post_save, sender=ProductModel)
def sync_product_with_elastic(sender, instance, created, **kwargs):
    def run_task():
        if instance.is_deleted or not instance.is_active:
            dispatch_task_safely(delete_product_from_elastic, instance.id)
        else:
            dispatch_task_safely(index_product_to_elastic, instance.id)

    transaction.on_commit(run_task)


@receiver(post_save, sender=ProductImageModel)
def sync_product_after_image_save(sender, instance, created, **kwargs):
    def run_task():
        product = instance.product

        dispatch_task_safely(index_product_to_elastic, product.id)

    transaction.on_commit(run_task)


@receiver(post_save, sender=ProductVideoModel)
def sync_product_after_video_save(sender, instance, created, **kwargs):
    def run_task():
        product = instance.product

        if product.is_deleted or not product.is_active:
            dispatch_task_safely(delete_product_from_elastic, product.id)
        else:
            dispatch_task_safely(index_product_to_elastic, product.id)

    transaction.on_commit(run_task)


@receiver(post_save, sender=ShopModel)
def sync_products_after_shop_change(sender, instance, created, **kwargs):
    reindex_products(ProductModel.objects.filter(shop=instance, is_deleted=False))


@receiver(post_save, sender=CategoryModel)
def sync_products_after_category_change(sender, instance, created, **kwargs):
    reindex_products(ProductModel.objects.filter(category=instance, is_deleted=False))
