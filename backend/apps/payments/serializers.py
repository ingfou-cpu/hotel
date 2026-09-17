"""Serializers DRF du domaine Paiements."""

from django.conf import settings

from rest_framework import serializers

from apps.bookings.models import Booking
from apps.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Représentation d'un paiement (lecture seule côté API)."""

    booking_code = serializers.CharField(source="booking.booking_code", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "booking",
            "booking_code",
            "user",
            "user_email",
            "amount",
            "currency",
            "status",
            "status_display",
            "payment_method",
            "stripe_payment_intent_id",
            "created_at",
        )
        read_only_fields = fields


class PaymentCreateSerializer(serializers.Serializer):
    """Préparation d'un paiement Checkout pour une réservation.

    Le montant est automatiquement égal au ``total_price`` de la réservation ;
    la devise vient de ``settings.STRIPE_CURRENCY``. Un seul paiement par
    réservation (relation OneToOne sur le modèle).
    """

    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())
    # Sortie lecture seule : référence et récapitulatif du paiement créé.
    id = serializers.IntegerField(read_only=True)
    booking_code = serializers.CharField(source="booking.booking_code", read_only=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    currency = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def validate_booking(self, booking):
        if hasattr(booking, "payment"):
            raise serializers.ValidationError(
                "Un paiement existe déjà pour cette réservation."
            )
        if booking.status != Booking.Status.PENDING:
            raise serializers.ValidationError(
                "Seule une réservation « en attente » peut être payée."
            )
        # Le payeur doit être le client de la réservation, ou un gestionnaire
        # de l'hôtel concerné, ou le staff.
        request = self.context.get("request")
        user = request.user if request else None
        if user and not (
            user.is_staff
            or booking.user_id == user.id
            or booking.hotel.manager_id == user.id
        ):
            raise serializers.ValidationError(
                "Cette réservation ne vous appartient pas."
            )
        return booking

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else validated_data.pop("user", None)
        booking = validated_data["booking"]
        return Payment.objects.create(
            user=user,
            booking=booking,
            amount=booking.total_price,
            currency=settings.STRIPE_CURRENCY,
        )