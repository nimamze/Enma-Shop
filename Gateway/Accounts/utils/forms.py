from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("phone", "email")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("phone", "email", "first_name", "last_name", "image", "is_seller")
