from rest_framework import serializers
from django.contrib.auth import get_user_model
from Accounts.utils.phone_number_validate import validate_iranian_phone

User = get_user_model()


class UserOtpValidationSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    phone = serializers.CharField(max_length=16)
    action = serializers.ChoiceField(
        choices=[
            ("SIGN_UP", "SIGN_UP"),
            ("PASSWORD", "PASSWORD"),
        ]
    )


class UserOtpSendSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=16)

    def validate_phone(self, value):
        phone = value.strip()
        validate_iranian_phone(phone)
        return phone


class UserSignUpSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=16)
    password1 = serializers.CharField(max_length=10, write_only=True)
    password2 = serializers.CharField(max_length=10, write_only=True)

    def validate_phone(self, value):
        phone = value.strip()
        validate_iranian_phone(phone)
        return phone

    def validate(self, attrs):
        if attrs["password1"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "image"]


class UserSellerSerializer(serializers.Serializer):
    choice = serializers.ChoiceField(
        choices=[
            ("ACTIVE", "Become a Seller"),
            ("RESIGN", "Resign Seller Status"),
        ]
    )


class UserForgotPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=16)
    password1 = serializers.CharField(max_length=10, write_only=True)
    password2 = serializers.CharField(max_length=10, write_only=True)

    def validate_phone(self, value):
        phone = value.strip()
        validate_iranian_phone(phone)
        return phone

    def validate(self, attrs):
        if attrs["password1"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return attrs
