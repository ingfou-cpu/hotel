"""Serializers DRF du domaine Avis."""

from django.core.exceptions import ValidationError
from rest_framework import serializers

from apps.bookings.models import Booking
from apps.hotels.models import Hotel
from apps.reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Avis d'un client sur un hôtel.

    Validation : note 1-5, réservation associée (terminée + client), un seul
    avis par (client, hôtel).
    """

    user = serializers.EmailField(source="user.email", read_only=True)
    hotel = serializers.PrimaryKeyRelatedField(
        queryset=Hotel.objects.all(), write_only=True
    )
    hotel_details = serializers.SerializerMethodField()
    booking = serializers.PrimaryKeyRelatedField(
        queryset=Booking.objects.all(), required=False, allow_null=True
    )
    rating = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = Review
        fields = (
            "id",
            "user",
            "hotel",
            "hotel_details",
            "booking",
            "rating",
            "comment",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def get_hotel_details(self, obj):
        return {
            "id": obj.hotel_id,
            "name": obj.hotel.name,
            "city": obj.hotel.city,
        }

    def validate(self, attrs):
        hotel = attrs.get("hotel")
        request = self.context.get("request")
        user = request.user if request else attrs.get("user")
        if hotel is not None and user is not None and self.instance is None:
            if Review.objects.filter(user=user, hotel=hotel).exists():
                raise serializers.ValidationError(
                    {"hotel": "Vous avez déjà publié un avis sur cet hôtel."}
                )
        # La réservation associée doit appartenir au client et être terminée.
        booking = attrs.get("booking")
        if booking is not None:
            if user is None or booking.user_id != user.id:
                raise serializers.ValidationError(
                    {"booking": "Cette réservation ne vous appartient pas."}
                )
            if booking.status != Booking.Status.COMPLETED:
                raise serializers.ValidationError(
                    {"booking": "Vous ne pouvez évaluer que des séjours terminés."}
                )
        return attrs

    def create(self, validated_data):
        # ``serializer.save(user=...)`` place ``user`` dans validated_data.
        user = validated_data.pop("user", None)
        if user is None:
            request = self.context.get("request")
            user = request.user if request else None
        review = Review(user=user, **validated_data)
        try:
            review.full_clean()  # valide aussi la réservation associée
        except ValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
        review.save()
        return review