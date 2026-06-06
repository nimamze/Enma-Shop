from django.db import models
from django.conf import settings
from Core.models import SoftDeleteModel
from Core.utils.file_cleanup import delete_file

User = settings.AUTH_USER_MODEL


class ShopModel(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shops")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=16, unique=True)
    email = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to="shops/logos/", null=True, blank=True)
    image = models.ImageField(upload_to="shops/images/main/", null=True, blank=True)
    website = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    telegram = models.URLField(blank=True, null=True)
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(11)],  # type: ignore
        default=0,
    )

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_shop = ShopModel.all_objects.get(pk=self.pk)
                if old_shop.logo and old_shop.logo != self.logo:
                    delete_file(old_shop.logo)
                if old_shop.image and old_shop.image != self.image:
                    delete_file(old_shop.image)
            except ShopModel.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        delete_file(self.logo)
        delete_file(self.image)
        for shop_image in self.images.all():  # type: ignore
            shop_image.delete()
        for shop_video in self.videos.all():  # type: ignore
            shop_video.delete()
        super().delete(using=using, keep_parents=keep_parents)

    def __str__(self):
        return f"{self.name} for user {self.user.phone}"


class ShopImageModel(SoftDeleteModel):
    shop = models.ForeignKey(ShopModel, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="shops/images/gallery/")
    order = models.PositiveIntegerField(default=0)

    def delete(self, using=None, keep_parents=False):
        delete_file(self.image)
        super().delete(using=using, keep_parents=keep_parents)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Image for {self.shop.name}"


class ShopVideoModel(SoftDeleteModel):
    shop = models.ForeignKey(ShopModel, on_delete=models.CASCADE, related_name="videos")
    video = models.FileField(upload_to="shops/videos/")
    order = models.PositiveIntegerField(default=0)

    def delete(self, using=None, keep_parents=False):
        delete_file(self.video)
        super().delete(using=using, keep_parents=keep_parents)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Video for {self.shop.name}"
