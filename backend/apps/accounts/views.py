"""Vues de l'API : comptes (inscription, profil, JWT, sécurité)."""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.serializers import ChangePasswordSerializer, UserSerializer
from apps.bookings.models import Booking


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """Connexion JWT limitée au même bucket strict que l'inscription."""

    throttle_scope = "auth"


class RegisterView(CreateAPIView):
    """Inscription d'un client : POST /api/v1/auth/register/."""

    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    throttle_scope = "auth"

    @extend_schema(
        summary="Inscription client",
        responses={201: UserSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        # Premier retour : l'utilisateur sans le mot de passe.
        data = UserSerializer(user, context=self.get_serializer_context()).data
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class MeView(RetrieveUpdateDestroyAPIView):
    """Profil de l'utilisateur connecté.

    GET / PATCH /api/v1/auth/me/ — lecture / modification du profil.
    DELETE /api/v1/auth/me/ — suppression du compte :
    - refusée tant qu'une réservation est en attente ou confirmée ;
    - désactive le compte (``is_active=False``), révoque les refresh tokens :
      les accès JWT deviennent inutilisables (SimpleJWT refuse les comptes
      inactifs) et la réinscription du même email est empêchée par l'unicité.
    """

    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    @extend_schema(
        summary="Supprimer mon compte",
        responses={
            204: OpenApiResponse(description="Compte désactivé"),
            400: OpenApiResponse(description="Réservations en cours"),
        },
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        en_cours = user.bookings.filter(
            status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED]
        )
        if en_cours.exists():
            return Response(
                {
                    "detail": (
                        "Suppression impossible : annulez d'abord vos réservations "
                        "en attente ou confirmées."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Révocation de tous les refresh tokens encore valides.
        for token in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=token)
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(APIView):
    """Changement de mot de passe.

    POST /api/v1/auth/change-password/  → ``{"current_password", "new_password",
    "new_password_confirm"}``. Révocation optionnelle du refresh token fourni :
    l'utilisateur se reconnecte après le changement.
    """

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Changer mon mot de passe",
        request=ChangePasswordSerializer,
        responses={204: OpenApiResponse(description="Mot de passe modifié")},
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        refresh = request.data.get("refresh")
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except TokenError:
                pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutView(APIView):
    """Révocation du token de rafraîchissement (liste noire JWT).

    POST /api/v1/auth/logout/  → ``{"refresh": "..."}`` → 204.
    """

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Déconnexion (révocation du refresh)",
        request=OpenApiTypes.OBJECT,
        responses={204: OpenApiResponse(description="Déconnecté")},
    )
    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except TokenError:
                # Token déjà invalide/expiré : l'état est déjà « déconnecté ».
                pass
        return Response(status=status.HTTP_204_NO_CONTENT)