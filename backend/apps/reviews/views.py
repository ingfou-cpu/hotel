"""Vues de l'API : avis clients."""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from apps.core.permissions import IsOwnerOrReadOnly
from apps.reviews.models import Review
from apps.reviews.serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """Avis sur les hôtels.

    - Lecture publique ; filtre ``?hotel=<id>``.
    - Création : client authentifié (validation note + réservation terminée).
    - Modification/suppression : auteur uniquement (ou staff).
    """

    serializer_class = ReviewSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    http_method_names = ("get", "post", "patch", "delete", "head", "options")

    def get_queryset(self):
        qs = Review.objects.select_related("user", "hotel")
        hotel_id = self.request.query_params.get("hotel")
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)