from django.urls import path
from Shops.views import ShopView, ShopImageView, ShopVideoView

urlpatterns = [
    path("", ShopView.as_view()),
    path("<int:id>/", ShopView.as_view()),
    path("<int:shop_id>/images/", ShopImageView.as_view()),
    path("<int:shop_id>/images/<int:image_id>/", ShopImageView.as_view()),
    path("<int:shop_id>/videos/", ShopVideoView.as_view()),
    path("<int:shop_id>/videos/<int:video_id>/", ShopVideoView.as_view()),
]
