from typing import Any


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
