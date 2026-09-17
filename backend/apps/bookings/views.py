"""Vues de l'API : réservations (création, cycle de vie, visibilité par rôle)."""

import stripe
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.bookings.serializers import BookingCreateSerializer, BookingSerializer
from apps.bookings.tasks import send_booking_confirmation
from apps.notifications.models import Notification
from apps.payments.models import Payment
from apps.payments.services import refund_payment


class BookingViewSet(viewsets.ModelViewSet):
    """Réservations.

    - Client : voit/gère ses propres réservations.
    - Gestionnaire : voit les réservations de ses hôtels (confirme, clôture).
    - Staff : tout.
    Actions : ``POST /bookings/{pk}/cancel/``, ``/confirm/``, ``/complete/``.
    Filtre : ``?status=pending|confirmed|cancelled|completed``.
    """

    permission_classes = (IsAuthenticated,)
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        user = self.request.user
        qs = Booking.objects.select_related("user", "hotel", "room")
        if user.is_staff:
            pass
        elif user.role == User.Role.HOTEL_MANAGER:
            qs = qs.filter(hotel__manager=user)
        else:
            qs = qs.filter(user=user)

        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        return BookingSerializer

    def perform_create(self, serializer):
        # L'utilisateur est imposé depuis le token (jamais depuis le corps).
        serializer.save(user=self.request.user)

    # -- Cycle de vie ---------------------------------------------------------

    def _get_manager_or_staff(self, booking, user):
        return user.is_staff or booking.hotel.manager_id == user.id

    @action(detail=True, methods=["post"])
    @extend_schema(
        summary="Annuler une réservation",
        description=(
            "Annulation libre-service si le délai n'est pas dépassé ; "
            "rembourse si payée."
        ),
        responses={
            200: BookingSerializer,
            400: OpenApiResponse(description="Délai dépassé ou remboursement refusé"),
        },
    )
    def cancel(self, request, pk=None):
        """Annulation libre-service (respecte le délai de la règle métier).

        Si la réservation est déjà payée, un remboursement Stripe est tenté
        avant l'annulation ; en cas de refus de Stripe, l'annulation est
        refusée (400) pour laisser le gestionnaire traiter le remboursement.
        """
        booking = self.get_object()
        if not (
            booking.user_id == request.user.id
            or self._get_manager_or_staff(booking, request.user)
        ):
            raise PermissionDenied("Vous ne pouvez pas annuler cette réservation.")
        if not booking.can_cancel():
            return Response(
                {"detail": (
                    f"Cette réservation ne peut plus être annulée (délai de "
                    f"{settings.BOOKING_CANCELLATION_DEADLINE_DAYS} jour(s) avant "
                    "l'arrivée dépassé)."
                )},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payment = getattr(booking, "payment", None)
        if payment and payment.status == Payment.Status.PAID:
            try:
                refund_payment(payment)
            except stripe.error.StripeError as exc:
                return Response(
                    {
                        "detail": (
                            "Annulation impossible : le remboursement a été "
                            f"refusé par Stripe ({exc.user_message or exc})."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        try:
            booking.cancel()
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST
            )
        Notification.objects.create(
            user=booking.user,
            type=Notification.Type.CANCELLATION,
            title="Réservation annulée",
            message=(
                f"Votre réservation {booking.booking_code} "
                f"({booking.hotel.name}) a été annulée."
            ),
        )
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    @extend_schema(
        summary="Confirmer une réservation",
        description="Par le gestionnaire de l'hôtel (après paiement).",
        responses={
            200: BookingSerializer,
            400: OpenApiResponse(description="Réservation non modifiable"),
        },
    )
    def confirm(self, request, pk=None):
        """Confirmation par le gestionnaire (après paiement réussi)."""
        booking = self.get_object()
        if not self._get_manager_or_staff(booking, request.user):
            raise PermissionDenied(
                "Seul le gestionnaire de l'hôtel peut confirmer une réservation."
            )
        try:
            booking.confirm()
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST
            )
        Notification.objects.create(
            user=booking.user,
            type=Notification.Type.BOOKING,
            title="Réservation confirmée",
            message=(
                f"Votre réservation {booking.booking_code} "
                f"({booking.hotel.name}) est confirmée."
            ),
        )
        send_booking_confirmation.delay(booking.pk)
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    @extend_schema(
        summary="Clôturer un séjour",
        description="Par le gestionnaire, séjour terminé.",
        responses={
            200: BookingSerializer,
            400: OpenApiResponse(description="Statut ou dates invalides"),
        },
    )
    def complete(self, request, pk=None):
        """Clôture d'un séjour terminé (gestionnaire)."""
        booking = self.get_object()
        if not self._get_manager_or_staff(booking, request.user):
            raise PermissionDenied(
                "Seul le gestionnaire de l'hôtel peut clôturer une réservation."
            )
        if not booking.complete():
            return Response(
                {"detail": "La réservation ne peut pas être clôturée "
                           "(statut ou dates invalides)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(BookingSerializer(booking).data)