from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
from django.conf import settings
from Addresses.models import Address
from Core.utils.redis import (
    get_cache,
    set_cache,
    MAP_REVERSE_CACHE_KEY,
    MAP_FORWARD_CACHE_KEY,
)
from Addresses.serializers import (
    AddressSerializer,
    CoordinatesToTextSerializer,
    TextToCoordinatesSerializer,
    ReverseGeocodeResponseSerializer,
    ForwardGeocodeResponseSerializer,
)
from Addresses.utils.address_service import AddressService
from Addresses.utils.map import extract_field


class CoordinatesToTextView(APIView):
    def post(self, request):
        serializer = CoordinatesToTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        latitude = float(serializer.validated_data["latitude"])  # type: ignore
        longitude = float(serializer.validated_data["longitude"])  # type: ignore
        result = self.reverse_geocode_from_map(latitude, longitude)
        if not result.get("ok"):
            return Response(
                {"detail": "Reverse geocoding failed.", "error": result.get("error")},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        response_data = {
            "province": result.get("province") or "",
            "city": result.get("city") or "",
            "street": result.get("street") or "",
            "postal_code": result.get("postal_code") or "",
            "full_address": result.get("full_address") or "",
        }
        serializer = ReverseGeocodeResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def reverse_geocode_from_map(latitude: float, longitude: float) -> dict:
        cache_key = MAP_REVERSE_CACHE_KEY.format(lat=latitude, lon=longitude)
        cached = get_cache(cache_key)
        if cached is not None:
            return cached
        api_key = getattr(settings, "MAP_API_KEY")
        reverse_url = getattr(settings, "MAP_REVERSE_URL")
        if not api_key or not reverse_url:
            return {"ok": False, "error": "map_api_not_configured"}
        try:
            response = requests.get(
                reverse_url,
                headers={"x-api-key": api_key},
                params={"lat": latitude, "lon": longitude},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            return {"ok": False, "error": str(exc)}

        province = extract_field(
            payload, "province", "state", "address.province", "address.state"
        )
        city = extract_field(
            payload,
            "city",
            "county",
            "district",
            "address.city",
            "address.county",
            "address.district",
        )
        street = extract_field(
            payload, "route_name", "street", "address.street", "address.road"
        )
        postal_code = extract_field(
            payload, "postal_code", "address.postal_code", "postalCode"
        )
        full_address = extract_field(
            payload,
            "formatted_address",
            "address_compact",
            "address",
            "postal_address",
        )
        result = {
            "ok": True,
            "province": province,
            "city": city,
            "street": street,
            "postal_code": postal_code,
            "full_address": full_address,
        }
        set_cache(
            cache_key,
            result,
            getattr(settings, "MAP_CACHE_TTL", 604800),
        )
        return result


class TextToCoordinatesView(APIView):
    def post(self, request):
        serializer = TextToCoordinatesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        address = serializer.validated_data["address"]  # type: ignore
        result = self.forward_geocode_from_map(address)
        if not result.get("ok"):
            return Response(
                {"detail": "Forward geocoding failed.", "error": result.get("error")},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        response_data = {
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude"),
        }
        response_serializer = ForwardGeocodeResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def forward_geocode_from_map(address: str) -> dict:
        cache_key = MAP_FORWARD_CACHE_KEY.format(
            address=address.strip().lower().replace(" ", "_")
        )
        cached = get_cache(cache_key)
        if cached is not None:
            return cached
        api_key = getattr(settings, "MAP_API_KEY")
        forward_url = getattr(settings, "MAP_FORWARD_URL")
        if not api_key:
            return {"ok": False, "error": "map_api_not_configured"}
        try:
            response = requests.get(
                forward_url,
                headers={"x-api-key": api_key},
                params={"query": address},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            return {"ok": False, "error": str(exc)}
        results = payload.get("results", [])
        if not results:
            return {"ok": False, "error": "no_results_found"}

        first_result = results[0]
        latitude = extract_field(first_result, "lat", "latitude", "x")
        longitude = extract_field(first_result, "lon", "lng", "longitude", "y")
        result = {
            "ok": True,
            "latitude": float(latitude),
            "longitude": float(longitude),
        }
        set_cache(
            cache_key,
            result,
            getattr(settings, "MAP_CACHE_TTL", 604800),
        )
        return result


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).order_by(
            "-is_default", "-updated_at"
        )

    def perform_create(self, serializer):
        AddressService.create_address(
            user=self.request.user, validated_data=serializer.validated_data
        )

    def perform_update(self, serializer):
        AddressService.update_address(
            instance=serializer.instance, validated_data=serializer.validated_data
        )
