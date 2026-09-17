"""Vues de l'API : paiements (Checkout Stripe, remboursement, webhook)."""

import json
import logging

import stripe
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.payments.models import Payment
from apps.payments.serializers import PaymentCreateSerializer, PaymentSerializer
from apps.payments.services import (
    configure_stripe,
    handle_checkout_event,
    prepare_checkout_session,
    refund_payment,
)

logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ModelViewSet):
    """Paiements.

    - Client : voit ses paiements ; POST prépare le paiement d'une réservation.
    - Gestionnaire : voit les paiements de ses hôtels ; POST rembourse.
    - Staff : tout.
    - ``POST /payments/{pk}/checkout/`` : crée la session Checkout Stripe.
    - ``POST /payments/{pk}/refund/`` : rembourse un paiement payé (manager/staff).
    """

    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        user = self.request.user
        qs = Payment.objects.select_related("user", "booking__hotel")
        if user.is_staff:
            return qs
        if user.role == User.Role.HOTEL_MANAGER:
            return qs.filter(booking__hotel__manager=user)
        return qs.filter(user=user)

    def get_serializer_class(self):
        if self.action == "create":
            return PaymentCreateSerializer
        return PaymentSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # -- Stripe ---------------------------------------------------------------

    @action(detail=True, methods=["post"])
    @extend_schema(
        summary="Créer la session Checkout Stripe",
        description="Retourne {checkout_url, session_id} ; idempotent tant que le paiement n'est pas échoué.",
        responses={
            201: OpenApiResponse(description="checkout_url + session_id"),
            400: OpenApiResponse(description="Déjà réglé ou statut incompatible"),
        },
    )
    def checkout(self, request, pk=None):
        """Crée (ou réutilise) la session Checkout Stripe du paiement.

        Retourne ``{"checkout_url": ..., "session_id": ...}`` vers laquelle le
        frontend redirige le client. Idempotent : la session existante est
        renvoyée tant que le paiement n'est pas échoué.
        """
        payment = self.get_object()
        if payment.status in (Payment.Status.PAID, Payment.Status.REFUNDED):
            return Response(
                {"detail": "Ce paiement est déjà réglé."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        session = prepare_checkout_session(payment)
        if session is None:
            return Response(
                {"detail": "Statut de paiement incompatible avec Checkout."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"checkout_url": session.url, "session_id": session.id},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    @extend_schema(
        summary="Rembourser un paiement payé",
        description="Manager de l'hôtel ou staff.",
        responses={
            200: PaymentSerializer,
            400: OpenApiResponse(description="Non payé ou refus Stripe"),
            403: OpenApiResponse(description="Non autorisé"),
        },
    )
    def refund(self, request, pk=None):
        """Rembourse un paiement payé (gestionnaire de l'hôtel ou staff)."""
        payment = self.get_object()
        user = request.user
        if not (user.is_staff or payment.booking.hotel.manager_id == user.id):
            raise PermissionDenied(
                "Seul le gestionnaire de l'hôtel concerné peut rembourser."
            )
        if payment.status != Payment.Status.PAID:
            return Response(
                {"detail": "Seul un paiement « Payé » peut être remboursé."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            refund_payment(payment)
        except stripe.error.StripeError as exc:
            if isinstance(exc, stripe.error.InvalidRequestError):
                return Response(
                    {"detail": exc.user_message or str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"detail": f"Remboursement refusé par Stripe : {exc.user_message or exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(PaymentSerializer(payment).data)


class StripeWebhookView(APIView):
    """Webhook Stripe : confirmation / échec / expiration des sessions Checkout.

    Aucune authentification par token : la fiabilité repose sur la vérification
    de la signature ``stripe-signature`` (``STRIPE_WEBHOOK_SECRET``).
    """

    authentication_classes = ()
    permission_classes = (AllowAny,)

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={
            204: OpenApiResponse(description="Événement traité"),
            400: OpenApiResponse(description="Signature ou payload invalide"),
            503: OpenApiResponse(description="Webhook non configuré"),
        },
        auth=None,
    )
    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        secret = settings.STRIPE_WEBHOOK_SECRET
        configure_stripe()

        if not secret:
            if not settings.DEBUG:
                return Response(
                    {"detail": "Webhook non configuré (STRIPE_WEBHOOK_SECRET)."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            # Développement : sans secret, on accepte le payload tel quel
            # (à sécuriser en production via `stripe listen`).
            logger.warning("STRIPE_WEBHOOK_SECRET manquant : vérification ignorée (DEBUG).")
            try:
                event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
            except ValueError:
                return Response(
                    {"detail": "Payload JSON invalide."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            try:
                event = stripe.Webhook.construct_event(payload, sig_header, secret)
            except (stripe.error.SignatureVerificationError, ValueError) as exc:
                return Response(
                    {"detail": f"Signature webhook invalide : {exc}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        handle_checkout_event(event)
        return Response(status=status.HTTP_204_NO_CONTENT)