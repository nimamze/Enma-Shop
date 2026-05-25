from django.core.exceptions import ValidationError
import re


def validate_iranian_phone(phone):
    if not re.fullmatch(r"09\d{9}", phone):
        raise ValidationError(
            "Invalid phone. Phone number must be an Iranian mobile number starting with 09"
        )
