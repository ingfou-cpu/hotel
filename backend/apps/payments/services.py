"""Services Stripe : session Checkout, gestion des webhooks, remboursements.

La logique métier est isolée des vues pour être testable sans HTTP :
``handle_checkout_event`` traite un évènement Stripe déjà construit.
"""

import logging
from decimal import Decimal

import stripe
from django.conf import settings

from apps.bookings.tasks import send_booking_confirmation
from apps.notifications.models import Notification
from apps.payments.models import Payment

logger = logging.getLogger(__name__)


def configure_stripe():
    """Stripe est configuré à chaque appel (clés lues depuis les settings)."""
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def _cents(amount):
    """Convertit un Decimal en centimes (entier attendu par l'API Stripe)."""
    return int((amount * Decimal(100)).to_integral_value())


def _notify(payment, type_, title, message):
    """Notification interne liée au paiement (user + éventuellement manager)."""
    Notification.objects.create(
        user=payment.user, type=type_, title=title, message=message
    )


def prepare_checkout_session(payment):
    """Crée (ou réutilise) la session Checkout d'un paiement en attente.

    Retourne la session Stripe, ou ``None`` si le paiement a un statut
    terminal (payé/remboursé). Une session existante encore active est
    réutilisée ; une session expirée/échec donne lieu à une nouvelle session.
    """
    if payment.status not in (Payment.Status.PENDING, Payment.Status.FAILED):
        return None
    configure_stripe()
    # Réutilisation uniquement d'une session encore active sur un paiement
    # toujours en attente ; un paiement échoué repart sur une session neuve.
    if payment.status == Payment.Status.PENDING and payment.stripe_session_id:
        try:
            existing = stripe.checkout.Session.retrieve(payment.stripe_session_id)
        except stripe.error.InvalidRequestError:
            existing = None
        if existing is not None and existing.url:
            return existing

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": payment.currency,
                    "unit_amount": _cents(payment.amount),
                    "product_data": {
                        "name": f"Réservation {payment.booking.booking_code}"
                    },
                },
                "quantity": 1,
            }
        ],
        customer_email=payment.user.email,
        metadata={
            "payment_id": str(payment.pk),
            "booking_code": payment.booking.booking_code,
        },
        success_url=(
            f"{settings.FRONTEND_URL}/reservation/success"
            "?session_id={CHECKOUT_SESSION_ID}"
        ),
        cancel_url=f"{settings.FRONTEND_URL}/reservation/annulation",
    )
    payment.stripe_session_id = session.id
    payment.save(update_fields=["stripe_session_id", "updated_at"])
    return session


def refund_payment(payment):
    """Rembourse un paiement payé auprès de Stripe et le marque remboursé.

    Lève ``stripe.error.StripeError`` si Stripe refuse ; l'appelant choisit de
    propager ou non l'erreur.
    """
    if not payment.stripe_payment_intent_id:
        raise stripe.error.InvalidRequestError(
            message=(
                "Ce paiement n'a pas de PaymentIntent Stripe "
                "(paiement simulé hors Stripe ?)."
            ),
            param="payment_intent",
        )
    configure_stripe()
    stripe.Refund.create(
        payment_intent=payment.stripe_payment_intent_id,
        amount=_cents(payment.amount),
        reason="requested_by_customer",
    )
    payment.status = Payment.Status.REFUNDED
    payment.save(update_fields=["status", "updated_at"])
    _notify(
        payment,
        Notification.Type.PAYMENT,
        "Remboursement effectué",
        f"La réservation {payment.booking.booking_code} a été remboursée "
        f"({payment.amount} {payment.currency}).",
    )


def handle_checkout_event(event):
    """Traite un évènement Checkout Stripe (idempotent).

    Retourne ``True`` si l'évènement concernait un paiement connu, ``False``
    sinon (session inconnue). Types gérés :
    - ``checkout.session.completed`` / ``async_payment_succeeded`` : paiement
      payé → réservation confirmée ; si la réservation a été annulée entre
      temps, remboursement automatique ;
    - ``checkout.session.expired`` / ``async_payment_failed`` : paiement échoué.
    """
    obj = event.data.object
    session_id = getattr(obj, "id", None)
    payment = (
        Payment.objects.filter(stripe_session_id=session_id)
        .select_related("user", "booking")
        .first()
    )
    if payment is None:
        return False

    if event.type in (
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    ):
        if payment.status == Payment.Status.PAID:
            return True  # Doublon Stripe déjà traité (idempotence).
        intent_id = getattr(obj, "payment_intent", None) or ""
        if payment.booking.status != payment.booking.Status.PENDING:
            # La réservation a été annulée après la création de la session :
            # remboursement automatique du client (échec = warn + retry Stripe).
            try:
                refund_payment(payment)
            except stripe.error.StripeError as exc:
                logger.warning(
                    "Remboursement auto échoué (reservation %s): %s",
                    payment.booking.booking_code, exc,
                )
                return True
            payment.stripe_payment_intent_id = intent_id
            payment.save(update_fields=["stripe_payment_intent_id", "updated_at"])
            return True
        payment.mark_paid(payment_intent_id=intent_id)
        user_full = payment.booking.user.full_name or payment.user.email
        _notify(
            payment,
            Notification.Type.PAYMENT,
            "Paiement confirmé",
            f"Votre réservation {payment.booking.booking_code} est payée "
            f"({payment.amount} {payment.currency}) et confirmée.",
        )
        # Email de confirmation (asynchrone, sans blocage du webhook).
        send_booking_confirmation.delay(payment.booking_id)
        # Notification au gestionnaire de l'hôtel concerné (s'il existe).
        manager = payment.booking.hotel.manager
        if manager is not None:
            Notification.objects.create(
                user=manager,
                type=Notification.Type.BOOKING,
                title="Réservation confirmée",
                message=(
                    f"Le client {user_full} a payé la réservation "
                    f"{payment.booking.booking_code} "
                    f"({payment.amount} {payment.currency})."
                ),
            )
        return True

    if event.type in (
        "checkout.session.expired",
        "checkout.session.async_payment_failed",
    ):
        if payment.status == Payment.Status.PENDING:
            payment.mark_failed()
            _notify(
                payment,
                Notification.Type.PAYMENT,
                "Paiement en échec",
                f"Le paiement de la réservation "
                f"{payment.booking.booking_code} a échoué. Vous pouvez réessayer.",
            )
        return True

    return False