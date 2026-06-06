from rest_framework import serializers
from Addresses.models import Address
from Addresses.utils.validators import validate_iran_coordinates


class CoordinatesToTextSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7)

    def validate(self, attrs):
        latitude = float(attrs.get("latitude"))
        longitude = float(attrs.get("longitude"))
        validate_iran_coordinates(latitude, longitude)
        return attrs


class TextToCoordinatesSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=500)


class ReverseGeocodeResponseSerializer(serializers.Serializer):
    province = serializers.CharField(max_length=255, allow_blank=True)
    city = serializers.CharField(max_length=255, allow_blank=True)
    street = serializers.CharField(max_length=255, allow_blank=True)
    postal_code = serializers.CharField(max_length=10, allow_blank=True, required=False)
    full_address = serializers.CharField(allow_blank=True, required=False)


class ForwardGeocodeResponseSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7)


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            "id",
            "title",
            "latitude",
            "longitude",
            "province",
            "city",
            "street",
            "alley",
            "number",
            "unit",
            "postal_code",
            "is_default",
        )
        read_only_fields = ["id"]

    def validate(self, attrs):
        lat = attrs.get("latitude")
        lon = attrs.get("longitude")

        if lat is not None or lon is not None:
            if lat is None or lon is None:
                raise serializers.ValidationError(
                    "latitude and longitude must be provided together."
                )
            validate_iran_coordinates(float(lat), float(lon))
        return attrs
