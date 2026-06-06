from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from Products.models import (
    ProductModel,
    ProductImageModel,
    ProductVideoModel,
)
from Products.tasks import (
    index_product_to_elastic,
    delete_product_from_elastic,
)


@receiver(post_save, sender=ProductModel)
def sync_product_with_elastic(sender, instance, created, **kwargs):
    def run_task():
        if instance.is_deleted or not instance.is_active:
            delete_product_from_elastic.delay(instance.id)  # type: ignore
        else:
            index_product_to_elastic.delay(instance.id)  # type: ignore

    transaction.on_commit(run_task)


@receiver(post_save, sender=ProductImageModel)
def sync_product_after_image_save(sender, instance, created, **kwargs):
    def run_task():
        product = instance.product

        if instance.is_deleted or product.is_deleted or not product.is_active:
            index_product_to_elastic.delay(product.id)  # type: ignore
        else:
            index_product_to_elastic.delay(product.id)  # type: ignore

    transaction.on_commit(run_task)


@receiver(post_save, sender=ProductVideoModel)
def sync_product_after_video_save(sender, instance, created, **kwargs):
    def run_task():
        product = instance.product

        if product.is_deleted or not product.is_active:
            delete_product_from_elastic.delay(product.id)  # type: ignore
        else:
            index_product_to_elastic.delay(product.id)  # type: ignore

    transaction.on_commit(run_task)
