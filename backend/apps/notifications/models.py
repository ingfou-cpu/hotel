"""Modèle Notification : notifications internes du tableau de bord."""

from django.db import models

from apps.accounts.models import User
from apps.core.models import TimeStampedModel


class NotificationQuerySet(models.QuerySet):
    """Requêtes réutilisables sur les notifications."""

    def unread(self):
        return self.filter(is_read=False)

    def mark_all_read(self, user):
        return self.filter(user=user, is_read=False).update(is_read=True)


class Notification(TimeStampedModel):
    """Notification interne affichée dans le tableau de bord de l'utilisateur."""

    class Type(models.TextChoices):
        INFO = "info", "Information"
        BOOKING = "booking", "Réservation"
        PAYMENT = "payment", "Paiement"
        CANCELLATION = "cancellation", "Annulation"
        REMINDER = "reminder", "Rappel"

    user = models.ForeignKey(
        User,
        verbose_name="Utilisateur",
        related_name="notifications",
        on_delete=models.CASCADE,
    )
    type = models.CharField(
        "Type", max_length=20, choices=Type.choices, default=Type.INFO
    )
    title = models.CharField("Titre", max_length=200)
    message = models.TextField("Message")
    link = models.CharField("Lien", max_length=255, blank=True)
    is_read = models.BooleanField("Lue", default=False)

    objects = NotificationQuerySet.as_manager()

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"{self.user.email} — {self.title}"