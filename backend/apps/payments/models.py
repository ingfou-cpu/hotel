"""Modèle Paiement (Stripe) lié à une réservation."""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.core.models import TimeStampedModel


class Payment(TimeStampedModel):
    """Paiement Stripe d'une réservation. Aucune donnée bancaire n'est stockée."""

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        PAID = "paid", "Payé"
        FAILED = "failed", "Échoué"
        REFUNDED = "refunded", "Remboursé"
        PARTIALLY_REFUNDED = "partially_refunded", "Partiellement remboursé"

    booking = models.OneToOneField(
        Booking,
        verbose_name="Réservation",
        related_name="payment",
        on_delete=models.PROTECT,
    )
    user = models.ForeignKey(
        User, verbose_name="Client", related_name="payments", on_delete=models.PROTECT
    )
    amount = models.DecimalField(
        "Montant",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    currency = models.CharField("Devise", max_length=3, default="eur")
    status = models.CharField(
        "Statut", max_length=25, choices=Status.choices, default=Status.PENDING,
        db_index=True,
    )
    stripe_session_id = models.CharField("Session Stripe Checkout", max_length=255, blank=True)
    stripe_payment_intent_id = models.CharField("PaymentIntent Stripe", max_length=255, blank=True)
    payment_method = models.CharField("Moyen de paiement", max_length=50, blank=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Paiement {self.stripe_payment_intent_id or self.pk} — {self.amount} {self.currency}"

    def mark_paid(self, payment_intent_id="", payment_method=""):
        """Marque le paiement payé et confirme la réservation associée."""
        self.status = self.Status.PAID
        if payment_intent_id:
            self.stripe_payment_intent_id = payment_intent_id
        if payment_method:
            self.payment_method = payment_method
        self.save(
            update_fields=["status", "stripe_payment_intent_id", "payment_method", "updated_at"]
        )
        self.booking.confirm()

    def mark_failed(self):
        """Marque le paiement échoué (la réservation reste « en attente », retry possible)."""
        self.status = self.Status.FAILED
        self.save(update_fields=["status", "updated_at"])