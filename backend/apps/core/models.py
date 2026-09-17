"""Socle commun des modèles (mixin d'horodatage)."""

from django.db import models


class TimeStampedModel(models.Model):
    """Mixin abstrait ajoutant les horodatages ``created_at`` / ``updated_at``."""

    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    updated_at = models.DateTimeField("Modifié le", auto_now=True)

    class Meta:
        abstract = True