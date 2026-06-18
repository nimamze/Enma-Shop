from django.urls import path
from Orders.views import (
    CartItemView,
    CartView,
    CheckoutView,
    OrderDetailView,
    OrderListView,
    OrderPaymentRetryView,
    ZarinPalVerifyView,
)

urlpatterns = [
    path("cart/", CartView.as_view(), name="orders-cart"),
    path("cart/items/", CartItemView.as_view(), name="orders-cart-items"),
    path("cart/items/<int:item_id>/", CartItemView.as_view(), name="orders-cart-item"),
    path("checkout/", CheckoutView.as_view(), name="orders-checkout"),
    path("verify/", ZarinPalVerifyView.as_view(), name="orders-zarinpal-verify"),
    path("", OrderListView.as_view(), name="orders-list"),
    path("<int:order_id>/", OrderDetailView.as_view(), name="orders-detail"),
    path(
        "<int:order_id>/retry-payment/",
        OrderPaymentRetryView.as_view(),
        name="orders-retry-payment",
    ),
]
