"""URLs de l'API : authentification JWT et profil."""

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from apps.accounts.views import (
    ChangePasswordView,
    LogoutView,
    MeView,
    RegisterView,
    ThrottledTokenObtainPairView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", ThrottledTokenObtainPairView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("verify/", TokenVerifyView.as_view(), name="auth-verify"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("me/", MeView.as_view(), name="auth-me"),
]