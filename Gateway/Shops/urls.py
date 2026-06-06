from django.urls import path
from Shops.views import ShopView, ShopImageView, ShopVideoView

urlpatterns = [
    path("shops/", ShopView.as_view()),
    path("shops/<int:id>/", ShopView.as_view()),
    path("shops/<int:shop_id>/images/", ShopImageView.as_view()),
    path("shops/<int:shop_id>/images/<int:image_id>/", ShopImageView.as_view()),
    path("shops/<int:shop_id>/videos/", ShopVideoView.as_view()),
    path("shops/<int:shop_id>/videos/<int:video_id>/", ShopVideoView.as_view()),
]
