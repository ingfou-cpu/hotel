"""Vues de l'API : notifications internes."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Notifications de l'utilisateur connecté.

    Actions : ``POST /notifications/mark_all_read/``,
    ``POST /notifications/{pk}/read/``.
    """

    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    @extend_schema(
        summary="Marquer toutes les notifications comme lues",
        responses={200: OpenApiResponse(description="{'updated': <int>}")},
    )
    def mark_all_read(self, request):
        updated = self.get_queryset().unread().count()
        self.get_queryset().mark_all_read(request.user)
        return Response({"updated": updated}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    @extend_schema(
        summary="Marquer une notification comme lue",
        responses={200: NotificationSerializer},
    )
    def read(self, request, pk=None):
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read", "updated_at"])
        return Response(NotificationSerializer(notification).data)