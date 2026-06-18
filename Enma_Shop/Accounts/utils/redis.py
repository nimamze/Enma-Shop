from django.conf import settings

USER_CHANGE_PASSWORD_LIMIT_KEY = "_user_change_password_limit_key"
USER_CHANGE_PASSWORD_OTP_VALIDATION_KEY = "_user_change_password_otp_validation_key"
USER_CHANGE_PASSWORD_TIME_LIMIT = int(settings.USER_CHANGE_PASSWORD_TIME_LIMIT)
USER_CHANGE_PASSWORD_LIMIT = int(settings.USER_CHANGE_PASSWORD_LIMIT)

USER_SELLER_LIMIT_KEY = "_user_seller_limit_key"
USER_SELLER_TIME_LIMIT = int(settings.USER_SELLER_TIME_LIMIT)
USER_SELLER_LIMIT = int(settings.USER_SELLER_LIMIT)

USER_SIGN_UP_OTP_VALIDATION_KEY = "_user_sign_up_otp_validation_key"

USER_OTP_CODE_LIMIT_KEY = "_user_otp_code_limit_key"
USER_OTP_CODE_LIMIT_TIME = int(settings.USER_OTP_CODE_LIMIT_TIME)
USER_OTP_CODE_LIMIT = int(settings.USER_OTP_CODE_LIMIT)
USER_OTP_PREVIOUS_CODE_KEY = "_user_otp_previous_code_key"
USER_OTP_CODE_TIME = int(settings.USER_OTP_CODE_TIME)
