from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    name = 'apps.reviews'
    verbose_name = 'Avis'

    def ready(self):
        from apps.reviews import signals  # noqa: F401
