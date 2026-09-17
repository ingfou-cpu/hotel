"""Administration Django du domaine Paiements."""

from django.contrib import admin

from apps.payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "booking", "user", "amount", "currency", "status",
        "stripe_payment_intent_id", "created_at",
    )
    list_filter = ("status", "currency")
    search_fields = ("booking__booking_code", "user__email", "stripe_payment_intent_id")
    list_select_related = ("booking", "user")
    readonly_fields = ("amount", "currency", "stripe_session_id", "stripe_payment_intent_id")