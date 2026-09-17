"""Modèle Avis : note 1-5 et commentaire après un séjour terminé."""

from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.core.models import TimeStampedModel
from apps.hotels.models import Hotel


class Review(TimeStampedModel):
    """Avis d'un client sur un hôtel. Un seul avis par (client, hôtel)."""

    user = models.ForeignKey(
        User, verbose_name="Client", related_name="reviews", on_delete=models.CASCADE
    )
    hotel = models.ForeignKey(
        Hotel, verbose_name="Hôtel", related_name="reviews", on_delete=models.CASCADE
    )
    booking = models.OneToOneField(
        Booking,
        verbose_name="Réservation associée",
        related_name="review",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    rating = models.PositiveSmallIntegerField("Note", default=5)
    comment = models.TextField("Commentaire", blank=True)

    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "hotel"], name="unique_review_per_user_hotel"
            ),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="review_rating_range",
            ),
        ]
        indexes = [models.Index(fields=["hotel", "-created_at"])]

    def __str__(self):
        return f"{self.user.email} — {self.hotel.name} ({self.rating}/5)"

    def clean(self):
        errors = {}
        if self.booking_id and (
            self.booking.user_id != self.user_id
            or self.booking.status != Booking.Status.COMPLETED
        ):
            errors["booking"] = (
                "Un avis ne peut être associé qu'à une réservation terminée "
                "du même client."
            )
        if errors:
            raise ValidationError(errors)