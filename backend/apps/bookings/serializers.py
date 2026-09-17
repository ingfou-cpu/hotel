"""Serializers DRF du domaine Réservations.

La création passe par ``BookingCreateSerializer`` qui applique toute la
validation métier de ``Booking.clean()`` (dates, capacité, anti
double-réservation) avant insertion. La lecture utilise ``BookingSerializer``
(données calculées inclues).
"""

from django.core.exceptions import ValidationError
from rest_framework import serializers

from apps.bookings.models import Booking
from apps.hotels.models import Hotel, Room


class BookingSerializer(serializers.ModelSerializer):
    """Représentation complète d'une réservation (lecture seule)."""

    user = serializers.EmailField(source="user.email", read_only=True)
    hotel = serializers.SerializerMethodField()
    room = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    traveler_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Booking
        fields = (
            "id",
            "booking_code",
            "user",
            "hotel",
            "room",
            "check_in",
            "check_out",
            "nights",
            "adults",
            "children",
            "traveler_count",
            "price_per_night",
            "tax_amount",
            "service_fee",
            "total_price",
            "status",
            "status_display",
            "created_at",
            "cancelled_at",
        )
        read_only_fields = fields

    def get_hotel(self, obj):
        return {
            "id": obj.hotel_id,
            "name": obj.hotel.name,
            "city": obj.hotel.city,
            "country": obj.hotel.country,
        }

    def get_room(self, obj):
        return {
            "id": obj.room_id,
            "room_number": obj.room.room_number,
            "room_type": obj.room.room_type,
            "price_per_night": str(obj.room.price_per_night),
        }


class BookingCreateSerializer(serializers.ModelSerializer):
    """Création d'une réservation : chambre + dates + nombre de voyageurs.

    La règle « une réservation ne remplace pas un prix » n'a pas lieu d'être :
    le prix à la nuit est automatiquement figé depuis la chambre au moment de
    la création (snapshot). Le champ ``hotel``/``user`` sont déduits.
    """

    room = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.filter(is_active=True)
    )
    adults = serializers.IntegerField(min_value=1)
    # Sortie en lecture seule : le créateur a immédiatement les références
    # (code, total, statut) pour agir ensuite sur la réservation.
    id = serializers.IntegerField(read_only=True)
    booking_code = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Booking
        fields = (
            "room",
            "check_in",
            "check_out",
            "adults",
            "children",
            "id",
            "booking_code",
            "status",
            "status_display",
            "total_price",
            "created_at",
        )

    def validate(self, attrs):
        room = attrs["room"]
        if not room.is_available:
            raise serializers.ValidationError(
                {"room": "Cette chambre n'est pas disponible à la réservation."}
            )

        # Applique toute la validation métier du modèle (dates, capacité,
        # anti double-réservation) en remontant les erreurs champ par champ.
        draft = Booking(
            room=room,
            check_in=attrs["check_in"],
            check_out=attrs["check_out"],
            adults=attrs.get("adults", 2),
            children=attrs.get("children", 0),
        )
        try:
            draft.full_clean(exclude=["user", "hotel", "price_per_night", "booking_code"])
        except ValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else validated_data.pop("user", None)
        room = validated_data["room"]
        booking = Booking(
            user=user,
            hotel=room.hotel,
            room=room,
            check_in=validated_data["check_in"],
            check_out=validated_data["check_out"],
            adults=validated_data.get("adults", 2),
            children=validated_data.get("children", 0),
            price_per_night=room.price_per_night,
        )
        booking.save()  # inclut full_clean() + calcul des totaux
        return booking