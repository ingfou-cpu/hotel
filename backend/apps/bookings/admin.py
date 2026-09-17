"""Administration Django du domaine Réservations."""

from django.contrib import admin

from apps.bookings.models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "booking_code", "user", "hotel", "room", "check_in", "check_out",
        "nights", "total_price", "status", "created_at",
    )
    list_filter = ("status", "check_in", "check_out")
    search_fields = ("booking_code", "user__email", "hotel__name", "room__room_number")
    date_hierarchy = "check_in"
    list_select_related = ("user", "hotel", "room")
    readonly_fields = ("booking_code", "nights", "tax_amount", "service_fee", "total_price")

    def has_delete_permission(self, request, obj=None):
        # Les réservations sont archivées (on applique des statuts), jamais supprimées.
        return False