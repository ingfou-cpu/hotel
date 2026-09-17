# Rend `celery -A config worker` opérationnel au démarrage du process Django.
from .celery import app as celery_app

__all__ = ("celery_app",)