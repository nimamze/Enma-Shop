from rest_framework.views import APIView
from rest_framework import status
from rest_framework.exceptions import NotFound
from Accounts.serializers import (
    UserOtpValidationSerializer,
    UserSignUpSerializer,
    UserProfileSerializer,
    UserSellerSerializer,
    UserForgotPasswordSerializer,
    UserOtpSendSerializer,
)
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from Accounts.utils.jwt_blacklist import blacklist_access_token
from django.db import transaction
from random import randint
from Core.tasks import send_sms
from Core.utils.redis import (
    USER_CHANGE_PASSWORD_LIMIT_KEY,
    USER_CHANGE_PASSWORD_TIME_LIMIT,
    USER_CHANGE_PASSWORD_LIMIT,
    USER_CHANGE_PASSWORD_OTP_VALIDATION_KEY,
    USER_SELLER_TIME_LIMIT,
    USER_SELLER_LIMIT_KEY,
    USER_SELLER_LIMIT,
    USER_SIGN_UP_OTP_VALIDATION_KEY,
    USER_OTP_CODE_LIMIT_KEY,
    USER_OTP_CODE_LIMIT_TIME,
    USER_OTP_CODE_LIMIT,
    USER_OTP_PREVIOUS_CODE_KEY,
    USER_OTP_CODE_TIME,
    set_cache,
    get_cache,
    delete_cache,
    increment_counter,
    get_counter,
)

User = get_user_model()


class LogOutView(APIView):
    def post(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                {"detail": "Access token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        access_token_str = auth_header.split(" ")[1]
        refresh_token_str = request.data.get("refresh")
        try:
            access_token = AccessToken(access_token_str)
            jti = access_token["jti"]
            exp = access_token["exp"]
            blacklist_access_token(jti, exp)  # type: ignore
            if refresh_token_str:
                refresh_token = RefreshToken(refresh_token_str)
                refresh_token.blacklist()
            return Response({"detail": "Logged out successfully."})
        except Exception:
            return Response(
                {"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
            )


class UserSignUpView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        phone = data.get("phone")  # type: ignore
        user_sign_up_otp_validation = get_cache(
            f"{phone}{USER_SIGN_UP_OTP_VALIDATION_KEY}"
        )
        if user_sign_up_otp_validation:
            password1 = data.get("password1")  # type: ignore
            try:
                with transaction.atomic():
                    User.objects.create_user(phone=phone, password=password1)  # type: ignore
            except Exception as exc:
                return Response(
                    {"detail": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            delete_cache(f"{phone}{USER_SIGN_UP_OTP_VALIDATION_KEY}")
            return Response(
                {"detail": "User created successfully."},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"detail": "OTP validation is required before sign-up."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserProfileView(APIView):
    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserOtpSendView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserOtpSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data.get("phone")  # type: ignore
        limit_key = f"{phone}{USER_OTP_CODE_LIMIT_KEY}"
        current_attempts = get_counter(limit_key)
        if current_attempts >= USER_OTP_CODE_LIMIT:
            return Response(
                {"detail": "OTP request limit exceeded. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        old_otp_code = get_cache(f"{phone}{USER_OTP_PREVIOUS_CODE_KEY}")
        if old_otp_code:
            return Response(
                {
                    "detail": "An OTP code has already been sent. Please wait before requesting another one."
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        new_otp_code = randint(1_000_000_000, 9_999_999_999)
        set_cache(
            f"{phone}{USER_OTP_PREVIOUS_CODE_KEY}",
            new_otp_code,
            USER_OTP_CODE_TIME,
        )
        send_sms.delay(
            phone=str(phone), message=f"Enma Shop\nYour code is {new_otp_code}"
        )  # type: ignore
        increment_counter(limit_key, 1, USER_OTP_CODE_LIMIT_TIME)
        return Response(
            {"detail": "OTP code sent successfully."}, status=status.HTTP_200_OK
        )


class UserOtpValidationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserOtpValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        phone = data.get("phone")  # type: ignore
        action = data.get("action")  # type: ignore
        user_otp = data.get("otp")  # type: ignore
        old_otp = get_cache(f"{phone}{USER_OTP_PREVIOUS_CODE_KEY}")
        if old_otp:
            if user_otp == old_otp:
                if action == "SIGN_UP":
                    key = f"{phone}{USER_SIGN_UP_OTP_VALIDATION_KEY}"
                else:
                    key = f"{phone}{USER_CHANGE_PASSWORD_OTP_VALIDATION_KEY}"
                set_cache(key, 1, USER_OTP_CODE_TIME)
                delete_cache(f"{phone}{USER_OTP_PREVIOUS_CODE_KEY}")
                return Response(
                    {"detail": "OTP code verified successfully."},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"detail": "OTP code does not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"detail": "OTP code has expired or has not been sent."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserSellerView(APIView):
    def post(self, request):
        user = request.user
        limit_key = f"{user.phone}{USER_SELLER_LIMIT_KEY}"
        current_attempts = get_counter(limit_key)
        if current_attempts >= USER_SELLER_LIMIT:
            return Response(
                {
                    "detail": "Seller status change limit exceeded. Please try again later."
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        serializer = UserSellerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        choice = serializer.validated_data.get("choice")  # type: ignore
        if choice == "ACTIVE":
            if user.is_seller:
                return Response(
                    {"detail": "You are already a seller."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                user.is_seller = True
                user.save()
                increment_counter(limit_key, 1, USER_SELLER_TIME_LIMIT)
                return Response(
                    {"detail": "Seller status activated successfully."},
                    status=status.HTTP_200_OK,
                )
        if choice == "RESIGN":
            if not user.is_seller:
                return Response(
                    {"detail": "You are not currently a seller."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                user.is_seller = False
                user.save()
                increment_counter(limit_key, 1, USER_SELLER_TIME_LIMIT)
                return Response(
                    {"detail": "Seller status removed successfully."},
                    status=status.HTTP_200_OK,
                )
        return Response(
            {"detail": "Invalid seller action."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserForgotPasswordView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        phone = data.get("phone")  # type: ignore

        limit_key = f"{phone}{USER_CHANGE_PASSWORD_LIMIT_KEY}"
        current_attempts = get_counter(limit_key)
        if current_attempts >= USER_CHANGE_PASSWORD_LIMIT:
            return Response(
                {"detail": "Password reset limit exceeded. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        user_change_password_otp_validation = get_cache(
            f"{phone}{USER_CHANGE_PASSWORD_OTP_VALIDATION_KEY}"
        )
        if user_change_password_otp_validation:
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist as exc:
                raise NotFound("User not found.") from exc

            password = data.get("password1")  # type: ignore
            with transaction.atomic():
                user.set_password(password)
                user.save()
                delete_cache(f"{phone}{USER_CHANGE_PASSWORD_OTP_VALIDATION_KEY}")
                increment_counter(
                    limit_key,
                    1,
                    USER_CHANGE_PASSWORD_TIME_LIMIT,
                )
            return Response(
                {"detail": "Password changed successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"detail": "OTP validation is required before changing the password."},
            status=status.HTTP_400_BAD_REQUEST,
        )
