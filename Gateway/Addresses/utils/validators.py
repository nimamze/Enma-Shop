from rest_framework import serializers
IRAN_MIN_LATITUDE = 24.8
IRAN_MAX_LATITUDE = 37.7
IRAN_MIN_LONGITUDE = 44.0
IRAN_MAX_LONGITUDE = 60.5



def validate_iran_coordinates(latitude: float, longitude: float) -> None:
    if not (
        IRAN_MIN_LATITUDE <= latitude <= IRAN_MAX_LATITUDE
        and IRAN_MIN_LONGITUDE <= longitude <= IRAN_MAX_LONGITUDE
    ):
        raise serializers.ValidationError("Coordinates must be within Iran boundaries.")
