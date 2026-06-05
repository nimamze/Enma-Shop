from django.conf import settings
from django.core.cache import cache
from typing import Any


# ============================================================================
# PASSWORD CHANGE OTP VALIDATION
# ============================================================================
USER_CHANGE_PASSWORD_LIMIT_KEY = "{user_id}_user_change_password_limit_key"
USER_CHANGE_PASSWORD_OTP_VALIDATION_KEY = (
    "{user_id}_user_change_password_otp_validation_key"
)
USER_CHANGE_PASSWORD_TIME_LIMIT = int(settings.USER_CHANGE_PASSWORD_TIME_LIMIT)
USER_CHANGE_PASSWORD_LIMIT = int(settings.USER_CHANGE_PASSWORD_LIMIT)


# ============================================================================
# SELLER VERIFICATION
# ============================================================================
USER_SELLER_LIMIT_KEY = "{user_id}_user_seller_limit_key"
USER_SELLER_TIME_LIMIT = int(settings.USER_SELLER_TIME_LIMIT)
USER_SELLER_LIMIT = int(settings.USER_SELLER_LIMIT)


# ============================================================================
# SIGN UP OTP VALIDATION
# ============================================================================
USER_SIGN_UP_OTP_VALIDATION_KEY = "{phone_number}_user_sign_up_otp_validation_key"


# ============================================================================
# OTP CODE LIMITS
# ============================================================================
USER_OTP_CODE_LIMIT_KEY = "{phone_number}_user_otp_code_limit_key"
USER_OTP_CODE_LIMIT_TIME = int(settings.USER_OTP_CODE_LIMIT_TIME)
USER_OTP_CODE_LIMIT = int(settings.USER_OTP_CODE_LIMIT)
USER_OTP_PREVIOUS_CODE_KEY = "{phone_number}_user_otp_previous_code_key"
USER_OTP_CODE_TIME = int(settings.USER_OTP_CODE_TIME)


# ============================================================================
# Map Cache Keys
# ============================================================================
MAP_REVERSE_CACHE_KEY = "map_reverse_{lat}_{lon}"
MAP_FORWARD_CACHE_KEY = "map_forward_{address}"


# ============================================================================
# CACHE OPERATIONS
# ============================================================================
def set_cache(key: str, value: Any, timeout: int | None = None) -> None:
    """Set a value in Redis cache."""
    cache.set(key, value, timeout)


def get_cache(key: str) -> Any:
    """Get a value from Redis cache."""
    return cache.get(key)


def delete_cache(key: str) -> None:
    """Delete a key from Redis cache."""
    cache.delete(key)


def increment_counter(key: str, delta: int = 1, timeout: int | None = None) -> int:
    """Increment a counter in Redis cache."""
    current = get_cache(key)
    if current is None:
        current = 0
    new_value = current + delta
    if timeout:
        set_cache(key, new_value, timeout)
    else:
        cache.set(key, new_value)
    return new_value


def get_counter(key: str) -> int:
    """Get counter value from Redis cache."""
    value = get_cache(key)
    return value if value is not None else 0
