"""Modèles du domaine Hôtels : équipements, hôtels, chambres, images, favoris."""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.accounts.models import User
from apps.core.models import TimeStampedModel


class Amenity(TimeStampedModel):
    """Équipement proposé par un hôtel ou une chambre (Wi-Fi, piscine…)."""

    name = models.CharField("Nom", max_length=100, unique=True)
    slug = models.SlugField("Slug", max_length=100, unique=True)
    icon = models.CharField("Icône", max_length=50, blank=True)

    class Meta:
        verbose_name = "Équipement"
        verbose_name_plural = "Équipements"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Hotel(TimeStampedModel):
    """Établissement hôtelier avec localisation, étoiles et équipements."""

    manager = models.ForeignKey(
        User,
        verbose_name="Gestionnaire",
        related_name="managed_hotels",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"role": User.Role.HOTEL_MANAGER},
    )
    name = models.CharField("Nom", max_length=200)
    description = models.TextField("Description")
    address = models.CharField("Adresse", max_length=255)
    city = models.CharField("Ville", max_length=100, db_index=True)
    country = models.CharField("Pays", max_length=100, db_index=True)
    latitude = models.DecimalField(
        "Latitude",
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(Decimal("-90")), MaxValueValidator(Decimal("90"))],
    )
    longitude = models.DecimalField(
        "Longitude",
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(Decimal("-180")), MaxValueValidator(Decimal("180"))],
    )
    stars = models.PositiveSmallIntegerField(
        "Étoiles",
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    amenities = models.ManyToManyField(
        Amenity, verbose_name="Équipements", related_name="hotels", blank=True
    )
    is_active = models.BooleanField("Actif", default=True)
    # Note moyenne et nombre d'avis : champs dénormalisés maintenus par
    # ``recalculate_rating()`` (signal déclenché à chaque création/suppression d'avis).
    average_rating = models.FloatField("Note moyenne", default=0.0)
    reviews_count = models.PositiveIntegerField("Nombre d'avis", default=0)

    class Meta:
        verbose_name = "Hôtel"
        verbose_name_plural = "Hôtels"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["city", "is_active"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(stars__gte=1) & models.Q(stars__lte=5),
                name="hotel_stars_range",
            ),
            models.CheckConstraint(
                condition=models.Q(latitude__gte=-90) & models.Q(latitude__lte=90),
                name="hotel_latitude_range",
            ),
            models.CheckConstraint(
                condition=models.Q(longitude__gte=-180) & models.Q(longitude__lte=180),
                name="hotel_longitude_range",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.city})"

    @property
    def room_count(self):
        return self.rooms.filter(is_active=True).count()

    @property
    def starting_price(self):
        """Prix le plus bas parmi les chambres actives, disponibles et non gratuites."""
        price = (
            self.rooms.filter(is_active=True, is_available=True)
            .order_by("price_per_night")
            .values_list("price_per_night", flat=True)
            .first()
        )
        return price if price is not None else Decimal("0")

    def recalculate_rating(self):
        """Re-calcule note moyenne et nombre d'avis à partir des avis existants."""
        agg = self.reviews.aggregate(
            avg=models.Avg("rating"), count=models.Count("id")
        )
        self.average_rating = round(agg["avg"] or 0.0, 2)
        self.reviews_count = agg["count"] or 0
        self.save(update_fields=["average_rating", "reviews_count", "updated_at"])


class HotelImage(TimeStampedModel):
    """Photo d'un hôtel (galerie ; une image peut être marquée principale)."""

    hotel = models.ForeignKey(
        Hotel, verbose_name="Hôtel", related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField("Image", upload_to="hotels/%Y/%m/")
    alt = models.CharField("Texte alternatif", max_length=255, blank=True)
    is_primary = models.BooleanField("Image principale", default=False)

    class Meta:
        verbose_name = "Image d'hôtel"
        verbose_name_plural = "Images d'hôtels"
        ordering = ["id"]

    def __str__(self):
        return f"{self.hotel.name} — {self.alt or self.image.name}"


class Room(TimeStampedModel):
    """Chambre rattachée à un hôtel, avec tarif, capacité et équipements."""

    class Type(models.TextChoices):
        SINGLE = "single", "Simple"
        DOUBLE = "double", "Double"
        SUITE = "suite", "Suite"
        FAMILY = "family", "Familiale"

    hotel = models.ForeignKey(
        Hotel, verbose_name="Hôtel", related_name="rooms", on_delete=models.CASCADE
    )
    room_number = models.CharField("Numéro de chambre", max_length=20)
    room_type = models.CharField(
        "Type", max_length=20, choices=Type.choices, default=Type.DOUBLE
    )
    description = models.TextField("Description", blank=True)
    price_per_night = models.DecimalField(
        "Prix par nuit",
        max_digits=10,
        decimal_places=2,
        db_index=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    max_occupancy = models.PositiveSmallIntegerField(
        "Capacité maximale", default=2, validators=[MinValueValidator(1)]
    )
    beds = models.PositiveSmallIntegerField(
        "Nombre de lits", default=1, validators=[MinValueValidator(1)]
    )
    amenities = models.ManyToManyField(
        Amenity, verbose_name="Équipements", related_name="rooms", blank=True
    )
    is_available = models.BooleanField("Disponible", default=True)
    is_active = models.BooleanField("Actif", default=True)

    class Meta:
        verbose_name = "Chambre"
        verbose_name_plural = "Chambres"
        ordering = ["hotel", "room_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["hotel", "room_number"], name="unique_room_number_per_hotel"
            ),
        ]
        indexes = [
            models.Index(fields=["hotel", "is_active"]),
            models.Index(fields=["price_per_night"]),
        ]

    def __str__(self):
        return f"{self.hotel.name} — chambre {self.room_number}"

    def is_available_for(self, check_in, check_out):
        """True si la chambre est active/disponible et sans réservation active
        sur l'intervalle [check_in, check_out)."""
        if not (self.is_active and self.is_available):
            return False
        from apps.bookings.models import Booking

        return not Booking.objects.overlapping(self, check_in, check_out).exists()


class RoomImage(TimeStampedModel):
    """Photo d'une chambre (galerie ; une image peut être marquée principale)."""

    room = models.ForeignKey(
        Room, verbose_name="Chambre", related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField("Image", upload_to="rooms/%Y/%m/")
    alt = models.CharField("Texte alternatif", max_length=255, blank=True)
    is_primary = models.BooleanField("Image principale", default=False)

    class Meta:
        verbose_name = "Image de chambre"
        verbose_name_plural = "Images de chambres"
        ordering = ["id"]

    def __str__(self):
        return f"Chambre {self.room.room_number} — {self.alt or self.image.name}"


class Favorite(TimeStampedModel):
    """Hôtel mis en favori par un utilisateur."""

    user = models.ForeignKey(
        User, verbose_name="Utilisateur", related_name="favorites", on_delete=models.CASCADE
    )
    hotel = models.ForeignKey(
        Hotel, verbose_name="Hôtel", related_name="favorited_by", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Favori"
        verbose_name_plural = "Favoris"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "hotel"], name="unique_user_hotel_favorite"),
        ]

    def __str__(self):
        return f"{self.user.email} → {self.hotel.name}"