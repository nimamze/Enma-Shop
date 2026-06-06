from django.db import models
from Core.models import SoftDeleteModel
from django.conf import settings

User = settings.AUTH_USER_MODEL


class ShopModel(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shops")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=16, unique=True)
    email = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to="shops/logos/", null=True, blank=True)
    image = models.ImageField(upload_to="shops/images/", null=True, blank=True)
    website = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    telegram = models.URLField(blank=True, null=True)
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(11)],  # type: ignore
        default=0,
    )

    def __str__(self):
        return f"{self.name} for user {self.user.username}"
