import phonenumbers
from django.core.exceptions import ValidationError
from phonenumbers import PhoneNumberType


def validate_iranian_phone(phone):
    try:
        parsed = phonenumbers.parse(phone, "IR")

        if not phonenumbers.is_valid_number(parsed):
            raise ValidationError("Invalid phone number.")

        if phonenumbers.region_code_for_number(parsed) != "IR":
            raise ValidationError("Phone number must be Iranian.")

        phone_type = phonenumbers.number_type(parsed)

        allowed_types = {
            PhoneNumberType.MOBILE,
            PhoneNumberType.FIXED_LINE,
            PhoneNumberType.FIXED_LINE_OR_MOBILE,
        }

        if phone_type not in allowed_types:
            raise ValidationError(
                "Phone number must be an Iranian mobile or landline number."
            )

    except phonenumbers.NumberParseException:
        raise ValidationError("Invalid phone number.")
