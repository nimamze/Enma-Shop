from typing import Any
import requests
from django.conf import settings


def extract_field(data: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = data
        for part in key.split("."):
            value = value.get(part) if isinstance(value, dict) else None
            if value is None:
                break
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def reverse_geocode(latitude: float, longitude: float):
    api_key = getattr(settings, "MAP_API_KEY", None)
    reverse_url = getattr(settings, "MAP_REVERSE_URL", None)
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
    neighbourhood = extract_field(
        payload,
        "neighbourhood",
        "address.neighbourhood",
        "address_complete",
        "neighborhood",
        "address.neighborhood",
    )
    street = extract_field(
        payload,
        "route_name",
        "street",
        "address.street",
        "address.road",
    )
    postal_code = extract_field(
        payload,
        "postal_code",
        "address.postal_code",
        "postalCode",
        "postal-code",
    )
    full_address = extract_field(
        payload,
        "formatted_address",
        "address_compact",
        "address",
        "postal_address",
    )
    return {
        "ok": True,
        "province": province,
        "city": city,
        "neighbourhood": neighbourhood,
        "street": street,
        "postal_code": postal_code,
        "full_address_from_map": full_address,
        "raw": payload,
    }
