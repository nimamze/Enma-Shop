from django.urls import path
from Shops.views import (
    PublicShopView,
    ShopImageView,
    ShopVideoView,
    ShopView,
)

urlpatterns = [
    path("catalog/", PublicShopView.as_view()),
    path("catalog/<int:id>/", PublicShopView.as_view()),
    path("", ShopView.as_view()),
    path("<int:id>/", ShopView.as_view()),
    path("<int:shop_id>/images/", ShopImageView.as_view()),
    path("<int:shop_id>/images/<int:image_id>/", ShopImageView.as_view()),
    path("<int:shop_id>/videos/", ShopVideoView.as_view()),
    path("<int:shop_id>/videos/<int:video_id>/", ShopVideoView.as_view()),
]
