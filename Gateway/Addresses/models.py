from django.conf import settings
from django.db import models

from Core.models import SoftDeleteModel

User = settings.AUTH_USER_MODEL


class Address(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    title = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    province = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    street = models.CharField(max_length=255)
    alley = models.CharField(max_length=255, blank=True, null=True)
    number = models.CharField(max_length=20)
    unit = models.CharField(max_length=20, blank=True, null=True)
    postal_code = models.CharField(max_length=10)
    full_address = models.TextField(blank=True, null=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        return f"{self.full_address} ({self.user.phone})"

    def build_full_address(self):
        parts = [
            self.province,
            self.city,
            self.street,
            self.alley,
            f"\u067e\u0644\u0627\u06a9 {self.number}" if self.number else None,
            f"\u0648\u0627\u062d\u062f {self.unit}" if self.unit else None,
        ]
        return "\u060c ".join([p for p in parts if p])

    def save(self, *args, **kwargs):
        self.full_address = self.build_full_address()
        super().save(*args, **kwargs)
