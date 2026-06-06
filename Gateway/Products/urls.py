from django.urls import path
from Products.views import (
    CategoryView,
    ProductView,
    ProductImageView,
    ProductVideoView,
    ProductSearchView,
)

urlpatterns = [
    path("categories/", CategoryView.as_view()),
    path("categories/<int:id>/", CategoryView.as_view()),
    path("products/", ProductView.as_view()),
    path("products/search/", ProductSearchView.as_view()),
    path("products/<int:id>/", ProductView.as_view()),
    path("products/<int:product_id>/images/", ProductImageView.as_view()),
    path(
        "products/<int:product_id>/images/<int:image_id>/",
        ProductImageView.as_view(),
    ),
    path("products/<int:product_id>/videos/", ProductVideoView.as_view()),
    path(
        "products/<int:product_id>/videos/<int:video_id>/",
        ProductVideoView.as_view(),
    ),
]
