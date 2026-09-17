"""Administration Django du domaine Avis."""

from django.contrib import admin

from apps.reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "hotel", "rating", "booking", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("user__email", "hotel__name", "comment")
    list_select_related = ("user", "hotel", "booking")