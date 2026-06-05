from rest_framework import serializers
from Addresses.constants import (
    IRAN_MIN_LATITUDE,
    IRAN_MAX_LATITUDE,
    IRAN_MIN_LONGITUDE,
    IRAN_MAX_LONGITUDE,
)


def validate_iran_coordinates(latitude: float, longitude: float) -> None:
    if not (
        IRAN_MIN_LATITUDE <= latitude <= IRAN_MAX_LATITUDE
        and IRAN_MIN_LONGITUDE <= longitude <= IRAN_MAX_LONGITUDE
    ):
        raise serializers.ValidationError("Coordinates must be within Iran boundaries.")
