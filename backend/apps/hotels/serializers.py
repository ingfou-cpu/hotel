"""Serializers DRF du domaine Hôtels."""

from rest_framework import serializers

from apps.accounts.models import User
from apps.hotels.models import Amenity, Favorite, Hotel, HotelImage, Room, RoomImage


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ("id", "name", "slug", "icon")


class HotelImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelImage
        fields = ("id", "image", "alt", "is_primary")


class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = ("id", "image", "alt", "is_primary")


class HotelMiniSerializer(serializers.ModelSerializer):
    """Représentation compacte d'un hôtel (utilisée en imbrication)."""

    image = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = ("id", "name", "city", "country", "image")

    def get_image(self, obj):
        primary = obj.images.filter(is_primary=True).first() or obj.images.first()
        if primary:
            request = self.context.get("request")
            return request.build_absolute_uri(primary.image.url) if request else primary.image.url
        return None


class RoomSerializer(serializers.ModelSerializer):
    """Chambre avec galerie d'images et équipements."""

    hotel = HotelMiniSerializer(read_only=True)
    hotel_id = serializers.PrimaryKeyRelatedField(
        queryset=Hotel.objects.all(), source="hotel", write_only=True
    )
    room_type_display = serializers.CharField(source="get_room_type_display", read_only=True)
    amenities = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Amenity.objects.all(), required=False, allow_empty=True
    )
    images = RoomImageSerializer(many=True, read_only=True)

    class Meta:
        model = Room
        fields = (
            "id",
            "hotel",
            "hotel_id",
            "room_number",
            "room_type",
            "room_type_display",
            "description",
            "price_per_night",
            "max_occupancy",
            "beds",
            "amenities",
            "images",
            "is_available",
            "is_active",
        )


class HotelSerializer(serializers.ModelSerializer):
    """Hôtel (détail) : images, équipements et chambres actives imbriqués."""

    manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.HOTEL_MANAGER),
        required=False,
        allow_null=True,
    )
    amenities = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Amenity.objects.all(), required=False, allow_empty=True
    )
    images = HotelImageSerializer(many=True, read_only=True)
    rooms = serializers.SerializerMethodField()
    room_count = serializers.IntegerField(read_only=True)
    starting_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    image = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = (
            "id",
            "manager",
            "name",
            "description",
            "address",
            "city",
            "country",
            "latitude",
            "longitude",
            "stars",
            "amenities",
            "images",
            "image",
            "rooms",
            "room_count",
            "starting_price",
            "average_rating",
            "reviews_count",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("average_rating", "reviews_count", "created_at", "updated_at")

    def get_image(self, obj):
        primary = obj.images.filter(is_primary=True).first() or obj.images.first()
        if primary:
            request = self.context.get("request")
            return request.build_absolute_uri(primary.image.url) if request else primary.image.url
        return None

    def get_rooms(self, obj):
        rooms = obj.rooms.filter(is_active=True)
        return RoomSerializer(rooms, many=True, context=self.context).data

    # -- Règles métier : miroir des contraintes du modèle -------------------

    def validate_stars(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Le nombre d'étoiles doit être entre 1 et 5.")
        return value

    def validate_latitude(self, value):
        if not -90 <= float(value) <= 90:
            raise serializers.ValidationError("La latitude doit être entre -90 et 90.")
        return value

    def validate_longitude(self, value):
        if not -180 <= float(value) <= 180:
            raise serializers.ValidationError("La longitude doit être entre -180 et 180.")
        return value

    def save(self, **kwargs):
        # Si aucun gestionnaire n'est fourni, on utilise l'utilisateur connecté
        # (gestionnaire d'hôtel ou staff) qui crée l'établissement.
        if "manager" not in self.validated_data:
            request = self.context.get("request")
            if request and request.user.is_authenticated:
                self.validated_data["manager"] = request.user
        return super().save(**kwargs)


class HotelListSerializer(HotelSerializer):
    """Liste d'hôtels : champs essentiels (recherche/listing)."""

    class Meta(HotelSerializer.Meta):
        fields = (
            "id",
            "name",
            "address",
            "city",
            "country",
            "stars",
            "image",
            "starting_price",
            "room_count",
            "average_rating",
            "reviews_count",
            "is_active",
            "created_at",
        )


class FavoriteSerializer(serializers.ModelSerializer):
    """Favori : l'utilisateur est imposé depuis le token (lecture seule)."""

    hotel = HotelMiniSerializer(read_only=True)
    hotel_id = serializers.PrimaryKeyRelatedField(
        queryset=Hotel.objects.filter(is_active=True), source="hotel", write_only=True
    )

    class Meta:
        model = Favorite
        fields = ("id", "hotel", "hotel_id", "created_at")
        read_only_fields = ("id", "created_at")

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else validated_data.pop("user", None)
        return Favorite.objects.get_or_create(user=user, hotel=validated_data["hotel"])[0]