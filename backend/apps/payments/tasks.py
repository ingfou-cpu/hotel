"""Tâches asynchrones des paiements (Celery)."""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.notifications.models import Notification
from apps.payments.models import Payment

logger = logging.getLogger(__name__)


@shared_task
def expire_stale_payments():
    """Marque « échoué » les paiements en attente depuis trop longtemps.

    Filet de sécurité : si le webhook Stripe n'a pas été reçu (secret absent,
    session expirée sans webhook…), le paiement reste bloqué en attente. Cette
    tâche périodique (beat, chaque nuit) le bascule en échoué afin que le
    client puisse relancer un paiement (nouvelle session Checkout).
    """
    limit = timezone.now() - timedelta(
        seconds=settings.PAYMENT_PENDING_TIMEOUT_SECONDS
    )
    stale = Payment.objects.filter(
        status=Payment.Status.PENDING, created_at__lt=limit
    ).select_related("user", "booking")
    count = 0
    for payment in stale:
        payment.mark_failed()
        Notification.objects.create(
            user=payment.user,
            type=Notification.Type.PAYMENT,
            title="Paiement expiré",
            message=(
                f"Le paiement de la réservation "
                f"{payment.booking.booking_code} a expiré. "
                "Vous pouvez relancer le paiement."
            ),
            link=f"{settings.FRONTEND_URL}/reservation/{payment.booking.booking_code}",
        )
        count += 1
    if count:
        logger.info("%d paiement(s) en attente marqué(s) échoué(s).", count)
    return count