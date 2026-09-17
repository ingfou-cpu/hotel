"""Administration Django du domaine Notifications."""

from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "title", "is_read", "created_at")
    list_filter = ("type", "is_read")
    search_fields = ("user__email", "title", "message")
    list_select_related = ("user",)