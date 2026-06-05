from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.password_validation import validate_password
from django.db import models
from Core.models import SoftDeleteModel
from Accounts.utils.phone_number_validate import validate_iranian_phone


class UserManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def create_user(self, phone, password, email=None, **kwargs):
        if not phone:
            raise ValueError("phone is required")
        if not password:
            raise ValueError("password is required")

        phone = phone.strip()
        validate_iranian_phone(phone)
        validate_password(password)
        email = self.normalize_email(email) if email else None
        user = self.model(phone=phone, email=email, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password, email=None, **kwargs):
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_superuser", True)
        if kwargs.get("is_staff") is not True:
            raise ValueError("is_staff must be True for Superuser.")
        if kwargs.get("is_active") is not True:
            raise ValueError("is_active must be True for Superuser.")
        if kwargs.get("is_superuser") is not True:
            raise ValueError("is_superuser must be True for Superuser.")
        return self.create_user(phone, password, email, **kwargs)


class UserModel(SoftDeleteModel, AbstractUser):
    username = None
    phone = models.CharField(max_length=16, unique=True)
    email = models.EmailField(blank=True, null=True)
    image = models.ImageField(upload_to="accounts/avatars/", null=True, blank=True)
    is_seller = models.BooleanField(default=False)
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def clean_phone(self):
        self.phone = self.phone.strip()
        validate_iranian_phone(self.phone)

    def clean(self):
        super().clean()
        self.clean_phone()

    def save(self, *args, **kwargs):
        self.clean_phone()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.phone
