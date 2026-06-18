from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from Accounts.views import (
    LogOutView,
    UserSignUpView,
    UserProfileView,
    UserOtpSendView,
    UserOtpValidationView,
    UserSellerView,
    UserForgotPasswordView,
)

urlpatterns = [
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("sign-up/", UserSignUpView.as_view(), name="sign_up"),
    path("log-out/", LogOutView.as_view(), name="log_out"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("otp-send/", UserOtpSendView.as_view(), name="otp_send"),
    path("otp-validation/", UserOtpValidationView.as_view(), name="otp_validation"),
    path("seller/", UserSellerView.as_view(), name="seller"),
    path("forgot-password/", UserForgotPasswordView.as_view(), name="forgot_password"),
]
