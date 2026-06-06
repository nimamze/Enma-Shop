from django.db import models
from Core.models import SoftDeleteModel
from Core.utils.file_cleanup import delete_file
from Shops.models import ShopModel


class CategoryModel(SoftDeleteModel):
    name = models.CharField(max_length=255, unique=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductModel(SoftDeleteModel):
    shop = models.ForeignKey(
        ShopModel, on_delete=models.CASCADE, related_name="products"
    )
    category = models.ForeignKey(
        CategoryModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(
        blank=True,
        null=True,
    )
    price = models.PositiveBigIntegerField()
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def delete(self, using=None, keep_parents=False):
        for product_image in self.images.all():  # type: ignore
            product_image.delete()
        for product_video in self.videos.all():  # type: ignore
            product_video.delete()
        super().delete(using=using, keep_parents=keep_parents)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ProductImageModel(SoftDeleteModel):
    product = models.ForeignKey(
        ProductModel, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/images/")
    order = models.PositiveIntegerField(default=0)

    def delete(self, using=None, keep_parents=False):
        delete_file(self.image)
        super().delete(using=using, keep_parents=keep_parents)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductVideoModel(SoftDeleteModel):
    product = models.ForeignKey(
        ProductModel, on_delete=models.CASCADE, related_name="videos"
    )
    video = models.FileField(upload_to="products/videos/")
    order = models.PositiveIntegerField(default=0)

    def delete(self, using=None, keep_parents=False):
        delete_file(self.video)
        super().delete(using=using, keep_parents=keep_parents)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Video for {self.product.name}"
