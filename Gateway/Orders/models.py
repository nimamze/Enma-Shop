from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from uuid import uuid4
from Addresses.models import Address
from Core.models import BaseModel, SoftDeleteModel
from Products.models import ProductModel
from Shops.models import ShopModel

User = settings.AUTH_USER_MODEL


class CartModel(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")

    def __str__(self):
        return f"Cart {self.id} for user {self.user}"  # type: ignore


class CartItemModel(BaseModel):
    product = models.ForeignKey(
        ProductModel, on_delete=models.CASCADE, related_name="cart_items"
    )
    cart = models.ForeignKey(
        CartModel, on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_active_product_per_cart",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="cart_item_quantity_gt_zero",
            ),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in cart {self.cart_id}"  # type: ignore


class OrderModel(SoftDeleteModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PENDING_VERIFICATION = "pending_verification", "Pending verification"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    order_number = models.CharField(max_length=32, unique=True, editable=False)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    payment_status = models.CharField(
        max_length=32,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )
    receiver_name = models.CharField(max_length=255, blank=True)
    receiver_phone = models.CharField(max_length=16, blank=True)
    address_title = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    street = models.CharField(max_length=255, blank=True)
    alley = models.CharField(max_length=255, blank=True)
    number = models.CharField(max_length=20, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    full_address = models.TextField(blank=True)
    items_total = models.PositiveBigIntegerField(default=0)
    shipping_amount = models.PositiveBigIntegerField(default=0)
    discount_amount = models.PositiveBigIntegerField(default=0)
    payable_amount = models.PositiveBigIntegerField(default=0)
    authority = models.CharField(max_length=255, null=True, blank=True, unique=True)
    ref_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    payment_url = models.URLField(max_length=500, null=True, blank=True)
    description = models.CharField(max_length=500, blank=True)
    callback_status = models.CharField(max_length=32, blank=True)
    payment_attempts = models.PositiveIntegerField(default=0)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["authority"]),
            models.Index(fields=["ref_id"]),
            models.Index(fields=["order_number"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(items_total__gte=0),
                name="order_items_total_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(shipping_amount__gte=0),
                name="order_shipping_amount_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(discount_amount__gte=0),
                name="order_discount_amount_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(payable_amount__gte=0),
                name="order_payable_amount_gte_zero",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        self.payable_amount = (
            max(self.items_total, 0)
            + max(self.shipping_amount, 0)
            - max(self.discount_amount, 0)
        )
        if self.payable_amount < 0:
            self.payable_amount = 0
        super().save(*args, **kwargs)

    @property
    def total_amount(self):
        return self.payable_amount

    def generate_order_number(self):
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        suffix = uuid4().hex[:6].upper()
        return f"ENMA-{timestamp}-{self.user_id or 'NEW'}-{suffix}" # type: ignore

    def __str__(self):
        return f"Order {self.order_number} by {self.user.phone}"  # type: ignore


class OrderItemModel(SoftDeleteModel):
    order = models.ForeignKey(
        OrderModel, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        ProductModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    shop = models.ForeignKey(
        ShopModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    product_name = models.CharField(max_length=255)
    shop_name = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.PositiveBigIntegerField()
    line_total = models.PositiveBigIntegerField()

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["order", "id"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="order_item_quantity_gt_zero",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0),
                name="order_item_unit_price_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(line_total__gte=0),
                name="order_item_line_total_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(line_total=F("quantity") * F("unit_price")),
                name="order_item_line_total_matches_quantity_price",
            ),
        ]

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} x {self.quantity} for order {self.order_id}"  # type: ignore
