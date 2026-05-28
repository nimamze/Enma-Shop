from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from Accounts.utils.jwt_blacklist import is_access_token_blacklisted


class RedisBlacklistJWTAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        token = super().get_validated_token(raw_token)
        jti = token.get("jti")
        if jti and is_access_token_blacklisted(jti):
            raise AuthenticationFailed("Token has been blacklisted (user logged out).")
        return token
