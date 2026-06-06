from django.urls import path
from Shops.views import ShopView


urlpatterns = [
    path("shops/", ShopView.as_view(), name="shop-list-create"),
    path("shops/<int:id>/", ShopView.as_view(), name="shop-detail"),
]
