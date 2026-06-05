from django.conf import settings
from django.db import models
from Core.models import BaseModel

User = settings.AUTH_USER_MODEL


class AddressUser(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    title = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, null=True
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, null=True
    )
    province = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    neighbourhood = models.CharField(max_length=255, blank=True)
    street = models.CharField(max_length=255, blank=True)
    alley = models.CharField(max_length=255, blank=True, null=True)
    plaque = models.CharField(max_length=20)
    unit = models.CharField(max_length=20, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_default"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.province} - {self.city} for user ({self.user.phone})"
