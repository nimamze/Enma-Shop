from django.urls import path, include
from rest_framework.routers import DefaultRouter
from Addresses.views import (
    AddressViewSet,
    CoordinatesToTextView,
    TextToCoordinatesView,
)

router = DefaultRouter()
router.register(r"addresses", AddressViewSet, basename="address")

urlpatterns = [
    path(
        "addresses/coordinates-to-text/",
        CoordinatesToTextView.as_view(),
        name="coordinates-to-text",
    ),
    path(
        "addresses/text-to-coordinates/",
        TextToCoordinatesView.as_view(),
        name="text-to-coordinates",
    ),
    path("", include(router.urls)),
]
