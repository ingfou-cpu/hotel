"""Serializers DRF du domaine Notifications."""

from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Notification interne (lecture).

    Le marquage « tout lu » ou « lu » est géré par les actions des vues,
    pas par une création/édition via l'API.
    """

    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Notification
        fields = ("id", "type", "type_display", "title", "message", "link", "is_read", "created_at")
        read_only_fields = fields