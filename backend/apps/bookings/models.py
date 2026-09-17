"""Modèle Réservation : anti-double-réservation, tarification figée, cycle de vie."""

import secrets
import string
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.accounts.models import User
from apps.core.models import TimeStampedModel
from apps.hotels.models import Hotel, Room


class BookingQuerySet(models.QuerySet):
    """Requêtes réutilisables sur les réservations."""

    def active(self):
        """Réservations qui « occupent » encore la chambre (attente ou confirmée)."""
        return self.filter(
            status__in=(Booking.Status.PENDING, Booking.Status.CONFIRMED)
        )

    def overlapping(self, room, check_in, check_out, exclude_pk=None):
        """Réservations actives dont l'intervalle chevauche [check_in, check_out)."""
        qs = self.active().filter(
            room=room,
            check_in__lt=check_out,
            check_out__gt=check_in,
        )
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        return qs


class Booking(TimeStampedModel):
    """Réservation d'une chambre par un client sur une période donnée."""

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        CONFIRMED = "confirmed", "Confirmée"
        CANCELLED = "cancelled", "Annulée"
        COMPLETED = "completed", "Terminée"

    booking_code = models.CharField(
        "Code de réservation", max_length=12, unique=True, editable=False
    )
    user = models.ForeignKey(
        User, verbose_name="Client", related_name="bookings", on_delete=models.PROTECT
    )
    hotel = models.ForeignKey(
        Hotel, verbose_name="Hôtel", related_name="bookings", on_delete=models.PROTECT
    )
    room = models.ForeignKey(
        Room, verbose_name="Chambre", related_name="bookings", on_delete=models.PROTECT
    )
    check_in = models.DateField("Arrivée", db_index=True)
    check_out = models.DateField("Départ")
    adults = models.PositiveSmallIntegerField("Adultes", default=2)
    children = models.PositiveSmallIntegerField("Enfants", default=0)
    # Prix par nuit figé au moment de la réservation (snapshot).
    price_per_night = models.DecimalField(
        "Prix par nuit (figé)", max_digits=10, decimal_places=2
    )
    nights = models.PositiveSmallIntegerField(
        "Nombre de nuits", editable=False, default=0
    )
    tax_amount = models.DecimalField(
        "Taxes", max_digits=10, decimal_places=2, default=0
    )
    service_fee = models.DecimalField(
        "Frais de service", max_digits=10, decimal_places=2, default=0
    )
    total_price = models.DecimalField(
        "Prix total", max_digits=10, decimal_places=2, editable=False, default=0
    )
    status = models.CharField(
        "Statut", max_length=20, choices=Status.choices, default=Status.PENDING,
        db_index=True,
    )
    cancelled_at = models.DateTimeField("Annulée le", null=True, blank=True)
    reminder_sent_at = models.DateTimeField(
        "Rappel d'arrivée envoyé le", null=True, blank=True
    )

    objects = BookingQuerySet.as_manager()

    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["hotel"]),
            models.Index(fields=["room", "check_in"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(check_out__gt=models.F("check_in")),
                name="booking_check_out_after_check_in",
            ),
            models.CheckConstraint(
                condition=models.Q(adults__gte=1),
                name="booking_at_least_one_adult",
            ),
        ]

    def __str__(self):
        return f"{self.booking_code} — {self.hotel.name} ({self.check_in} → {self.check_out})"

    # -- Calculs -----------------------------------------------------------

    @property
    def traveler_count(self):
        return self.adults + self.children

    def calculate_totals(self):
        """Retourne (sous-total, taxes, frais de service, total) selon les règles configurées."""
        subtotal = (self.price_per_night or 0) * (self.nights or 0)
        tax_rate = Decimal(str(settings.BOOKING_TAX_RATE))
        service_fee = Decimal(str(settings.BOOKING_SERVICE_FEE))
        tax = round(subtotal * tax_rate, 2)
        return subtotal, tax, service_fee, round(subtotal + tax + service_fee, 2)

    # -- Code unique --------------------------------------------------------

    @staticmethod
    def generate_booking_code():
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(10))

    # -- Validation métier ---------------------------------------------------

    def clean(self):
        errors = {}

        if self.check_in and self.check_out and self.check_out <= self.check_in:
            errors["check_out"] = "La date de départ doit être postérieure à la date d'arrivée."

        today = timezone.localdate()
        if self.check_in and self.check_in < today:
            errors["check_in"] = "La date d'arrivée ne peut pas être dans le passé."

        if self.adults is not None and self.adults < 1:
            errors["adults"] = "Au moins un adulte est requis."

        if self.room_id and self.adults is not None and self.children is not None:
            if self.traveler_count > self.room.max_occupancy:
                errors["adults"] = (
                    f"Cette chambre accueille au maximum {self.room.max_occupancy} "
                    f"personnes (adultes + enfants : {self.traveler_count})."
                )

        # Anti-double-réservation (niveau application).
        # Un niveau base de données PostgreSQL est ajouté en migration 0002
        # (contrainte d'exclusion gist).
        if not errors and self.room_id and self.check_in and self.check_out:
            overlap = Booking.objects.overlapping(
                self.room, self.check_in, self.check_out, exclude_pk=self.pk
            )
            if overlap.exists():
                errors["room"] = "Cette chambre est déjà réservée sur la période sélectionnée."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.booking_code:
            self.booking_code = self.generate_booking_code()

        if self.check_in and self.check_out:
            self.nights = max((self.check_out - self.check_in).days, 0)

        if not self.price_per_night and self.room_id:
            # Snapshot du prix de la chambre au moment de la réservation.
            # (Decimal(str(...)) : l'instance mise en cache garde la valeur brute.)
            self.price_per_night = Decimal(str(self.room.price_per_night))

        _subtotal, tax, service_fee, total = self.calculate_totals()
        self.tax_amount, self.service_fee, self.total_price = tax, service_fee, total

        if self._state.adding:
            self.full_clean()
        super().save(*args, **kwargs)

    # -- Cycle de vie --------------------------------------------------------

    def confirm(self):
        """Confirme une réservation en attente (après paiement réussi)."""
        if self.status != self.Status.PENDING:
            raise ValidationError(
                "Seule une réservation « en attente » peut être confirmée."
            )
        self.status = self.Status.CONFIRMED
        self.save(update_fields=["status", "updated_at"])

    def can_cancel(self):
        """Annulation libre-service autorisée jusqu'à N jours avant l'arrivée."""
        deadline = timezone.localdate() + timedelta(
            days=settings.BOOKING_CANCELLATION_DEADLINE_DAYS
        )
        return (
            self.status in (self.Status.PENDING, self.Status.CONFIRMED)
            and self.check_in >= deadline
        )

    def cancel(self):
        """Annule la réservation si la règle de délai le permet."""
        if not self.can_cancel():
            raise ValidationError(
                "Cette réservation ne peut plus être annulée en libre-service "
                f"(délai de {settings.BOOKING_CANCELLATION_DEADLINE_DAYS} jour(s) "
                "avant l'arrivée dépassé)."
            )
        self.status = self.Status.CANCELLED
        self.cancelled_at = timezone.now()
        self.save(update_fields=["status", "cancelled_at", "updated_at"])

    def complete(self):
        """Clôture une réservation confirmée dont le séjour est terminé."""
        if self.status == self.Status.CONFIRMED and self.check_out <= timezone.localdate():
            self.status = self.Status.COMPLETED
            self.save(update_fields=["status", "updated_at"])
            return True
        return False