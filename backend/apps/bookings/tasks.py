"""Tâches asynchrones des réservations (Celery).

- ``send_booking_confirmation`` : email de confirmation (déclenché à la
  confirmation d'une réservation, paiement Stripe ou gestionnaire).
- ``send_upcoming_reminder`` : rappel d'arrivée proche (email + notification),
  envoyé une seule fois par réservation grâce à ``reminder_sent_at``.
- ``scan_upcoming_reminders`` : tâche périodique qui planifie les rappels pour
  les séjours commençant dans les prochains jours.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.bookings.models import Booking
from apps.notifications.models import Notification

logger = logging.getLogger(__name__)


def _recipient(booking):
    """Destinataire : nom complet si renseigné, sinon l'email."""
    return booking.user.full_name or booking.user.email


@shared_task
def send_booking_confirmation(booking_id):
    """Envoie l'email de confirmation d'une réservation confirmée.

    Idempotent par construction : sans effet si la réservation n'est pas
    confirmée (ou n'existe plus).
    """
    booking = (
        Booking.objects.select_related("user", "hotel", "room")
        .filter(pk=booking_id, status=Booking.Status.CONFIRMED)
        .first()
    )
    if booking is None:
        logger.warning(
            "Confirmation ignorée : réservation %s introuvable ou non confirmée.",
            booking_id,
        )
        return False

    subject = f"Confirmation de votre réservation {booking.booking_code}"
    message = (
        f"Bonjour {_recipient(booking)},\n\n"
        f"Votre réservation {booking.booking_code} à l'hôtel "
        f"{booking.hotel.name} est confirmée.\n"
        f"Séjour : du {booking.check_in} au {booking.check_out} "
        f"({booking.nights} nuit(s)) — chambre {booking.room.room_number}.\n"
        f"Nombre de voyageurs : {booking.traveler_count}.\n"
        f"Total : {booking.total_price} {settings.STRIPE_CURRENCY}.\n\n"
        f"Merci de votre confiance,\nL'équipe {settings.SITE_NAME}"
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [booking.user.email],
        fail_silently=not settings.DEBUG,
    )
    logger.info("Email de confirmation envoyé pour %s.", booking.booking_code)
    return True


@shared_task
def send_upcoming_reminder(booking_id):
    """Rappel d'arrivée proche : email + notification, une seule fois.

    Le drapeau ``reminder_sent_at`` garantit l'unicité même si l'exécution
    est relancée (retry Celery, double scan périodique).
    """
    booking = (
        Booking.objects.select_related("user", "hotel")
        .filter(
            pk=booking_id,
            status=Booking.Status.CONFIRMED,
            reminder_sent_at__isnull=True,
        )
        .first()
    )
    if booking is None:
        return False

    subject = f"Votre séjour à {booking.hotel.name} commence bientôt"
    message = (
        f"Bonjour {_recipient(booking)},\n\n"
        f"Rappel : votre réservation {booking.booking_code} à l'hôtel "
        f"{booking.hotel.name} débute le {booking.check_in} "
        f"(départ le {booking.check_out}).\n"
        "Nous vous souhaitons un agréable séjour !\n\n"
        f"L'équipe {settings.SITE_NAME}"
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [booking.user.email],
        fail_silently=not settings.DEBUG,
    )
    Notification.objects.create(
        user=booking.user,
        type=Notification.Type.REMINDER,
        title=f"Séjour imminent — {booking.hotel.name}",
        message=(
            f"Votre réservation {booking.booking_code} commence le "
            f"{booking.check_in}."
        ),
        link=f"{settings.FRONTEND_URL}/reservation/{booking.booking_code}",
    )
    booking.reminder_sent_at = timezone.now()
    booking.save(update_fields=["reminder_sent_at", "updated_at"])
    logger.info("Rappel d'arrivée envoyé pour %s.", booking.booking_code)
    return True


@shared_task
def scan_upcoming_reminders(days=2):
    """Planifie les rappels des séjours commençant dans moins de ``days`` jours.

    Tâche périodique (beat) : elle ne fait que lancer ``send_upcoming_reminder``
    pour chaque réservation éligible ; l'unicité est assurée par le drapeau
    ``reminder_sent_at``.
    """
    today = timezone.localdate()
    window_end = today + timedelta(days=days)
    booking_ids = list(
        Booking.objects.filter(
            status=Booking.Status.CONFIRMED,
            reminder_sent_at__isnull=True,
            check_in__gte=today,
            check_in__lte=window_end,
        ).values_list("id", flat=True)
    )
    for booking_id in booking_ids:
        send_upcoming_reminder.delay(booking_id)
    return len(booking_ids)