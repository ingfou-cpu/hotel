"""Signaux du domaine Avis : maintien de la note moyenne de l'hôtel."""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.reviews.models import Review


@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_hotel_rating(sender, instance, **kwargs):
    """Re-calcule la note moyenne et le nombre d'avis de l'hôtel associé."""
    hotel = instance.hotel
    if hotel:
        hotel.recalculate_rating()