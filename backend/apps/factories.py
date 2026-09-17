"""Factories factory_boy pour tous les modèles HotelBooking."""

import factory
import random
from factory.django import DjangoModelFactory
from factory import Faker, LazyAttribute, Sequence, SubFactory, post_generation
from decimal import Decimal
from datetime import date, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

from apps.accounts.models import User
from apps.hotels.models import Amenity, Hotel, HotelImage, Room, RoomImage, Favorite
from apps.bookings.models import Booking
from apps.payments.models import Payment
from apps.reviews.models import Review
from apps.notifications.models import Notification


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def _dummy_image():
    """Génère une image JPEG minimale en mémoire pour les ImageField."""
    img = Image.new("RGB", (100, 100), color="blue")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(
        name=f"test_{random.random()}.jpg",
        content=buffer.read(),
        content_type="image/jpeg",
    )


def _future_check_in():
    """Génère une date d'arrivée future (entre 1 et 30 jours)."""
    return date.today() + timedelta(days=random.randint(1, 30))


def _check_out_from_check_in(check_in):
    """Génère une date de départ 1-7 jours après l'arrivée."""
    return check_in + timedelta(days=random.randint(1, 7))


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

class UserFactory(DjangoModelFactory):
    """Factory pour le modèle User personnalisé (auth par email)."""

    class Meta:
        model = User
        django_get_or_create = ("email",)
        skip_postgeneration_save = True

    email = Sequence(lambda n: f"user{n}@example.com")
    first_name = Faker("first_name", locale="fr_FR")
    last_name = Faker("last_name", locale="fr_FR")
    role = User.Role.CLIENT
    phone = Faker("phone_number", locale="fr_FR")
    is_staff = False
    is_superuser = False
    is_active = True

    @factory.lazy_attribute
    def password(self):
        return "testpass123"

    @post_generation
    def set_password(self, create, extracted, **kwargs):
        if create:
            self.set_password(self.password)
            self.save()

    @classmethod
    def create_client(cls, **kwargs):
        return cls.create(role=User.Role.CLIENT, **kwargs)

    @classmethod
    def create_hotel_manager(cls, **kwargs):
        return cls.create(role=User.Role.HOTEL_MANAGER, **kwargs)

    @classmethod
    def create_admin(cls, **kwargs):
        return cls.create(role=User.Role.ADMIN, is_staff=True, is_superuser=True, **kwargs)


# ---------------------------------------------------------------------------
# Hotels
# ---------------------------------------------------------------------------

class AmenityFactory(DjangoModelFactory):
    """Factory pour Amenity."""

    class Meta:
        model = Amenity
        django_get_or_create = ("name",)
        skip_postgeneration_save = True

    name = Sequence(lambda n: f"Amenity {n}")
    slug = factory.LazyAttribute(lambda o: f"amenity-{o.name.lower().replace(' ', '-')}")
    icon = ""


class HotelFactory(DjangoModelFactory):
    """Factory pour Hotel."""

    class Meta:
        model = Hotel
        skip_postgeneration_save = True

    manager = SubFactory(UserFactory, role=User.Role.HOTEL_MANAGER)
    name = Sequence(lambda n: f"Hôtel {n}")
    description = Faker("paragraph", nb_sentences=3, locale="fr_FR")
    address = Faker("street_address", locale="fr_FR")
    city = Faker("city", locale="fr_FR")
    country = "France"
    latitude = Decimal("48.8566")
    longitude = Decimal("2.3522")
    stars = 3
    is_active = True
    average_rating = Decimal("0.00")
    reviews_count = 0

    @post_generation
    def amenities(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.amenities.set(extracted)
        else:
            # Ajoute 2-3 équipements par défaut
            for _ in range(3):
                self.amenities.add(AmenityFactory.create())


class HotelImageFactory(DjangoModelFactory):
    """Factory pour HotelImage (image optionnelle pour éviter écritures disque)."""

    class Meta:
        model = HotelImage
        skip_postgeneration_save = True

    hotel = SubFactory(HotelFactory)
    image = factory.LazyAttribute(lambda _: _dummy_image())
    alt = Faker("sentence", nb_words=4, locale="fr_FR")
    is_primary = False


class RoomFactory(DjangoModelFactory):
    """Factory pour Room."""

    class Meta:
        model = Room
        skip_postgeneration_save = True

    hotel = SubFactory(HotelFactory)
    room_number = Sequence(lambda n: f"{100 + n}")
    room_type = Room.Type.DOUBLE
    description = Faker("paragraph", nb_sentences=2, locale="fr_FR")
    price_per_night = Decimal("120.00")
    max_occupancy = 2
    beds = 1
    is_available = True
    is_active = True

    @post_generation
    def amenities(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.amenities.set(extracted)
        else:
            for _ in range(2):
                self.amenities.add(AmenityFactory.create())


class RoomImageFactory(DjangoModelFactory):
    """Factory pour RoomImage (image optionnelle)."""

    class Meta:
        model = RoomImage
        skip_postgeneration_save = True

    room = SubFactory(RoomFactory)
    image = factory.LazyAttribute(lambda _: _dummy_image())
    alt = Faker("sentence", nb_words=4, locale="fr_FR")
    is_primary = False


class FavoriteFactory(DjangoModelFactory):
    """Factory pour Favorite."""

    class Meta:
        model = Favorite
        skip_postgeneration_save = True

    user = SubFactory(UserFactory, role=User.Role.CLIENT)
    hotel = SubFactory(HotelFactory)


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------

class BookingFactory(DjangoModelFactory):
    """Factory pour Booking."""

    class Meta:
        model = Booking
        skip_postgeneration_save = True

    user = SubFactory(UserFactory, role=User.Role.CLIENT)
    hotel = SubFactory(HotelFactory)
    room = factory.LazyAttribute(lambda o: RoomFactory.create(hotel=o.hotel))
    check_in = LazyAttribute(lambda _: _future_check_in())
    check_out = LazyAttribute(lambda o: _check_out_from_check_in(o.check_in))
    adults = 2
    children = 0
    status = Booking.Status.PENDING
    price_per_night = factory.LazyAttribute(lambda o: o.room.price_per_night if o.room else Decimal("120.00"))

    @factory.lazy_attribute
    def nights(self):
        return (self.check_out - self.check_in).days

    @post_generation
    def ensure_no_overlap(self, create, extracted, **kwargs):
        """
        S'assure que les dates ne chevauchent pas une réservation existante
        pour la même chambre (important pour les tests d'unicité).
        """
        if not create:
            return
        # Le save() du modèle lance full_clean() qui vérifie les chevauchements
        # Si ça échoue, on décale les dates
        from django.core.exceptions import ValidationError
        try:
            self.full_clean()
        except ValidationError:
            # Décale de 10 jours vers le futur
            self.check_in += timedelta(days=10)
            self.check_out += timedelta(days=10)
            self.nights = (self.check_out - self.check_in).days
            self.save()


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

class PaymentFactory(DjangoModelFactory):
    """Factory pour Payment."""

    class Meta:
        model = Payment
        skip_postgeneration_save = True

    booking = SubFactory(BookingFactory, status=Booking.Status.PENDING)
    user = factory.SelfAttribute("booking.user")
    amount = factory.LazyAttribute(lambda o: o.booking.total_price if o.booking else Decimal("150.00"))
    currency = "eur"
    status = Payment.Status.PENDING
    stripe_session_id = Sequence(lambda n: f"cs_test_{n}")
    stripe_payment_intent_id = Sequence(lambda n: f"pi_test_{n}")
    payment_method = "card"


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

class ReviewFactory(DjangoModelFactory):
    """Factory pour Review."""

    class Meta:
        model = Review
        skip_postgeneration_save = True

    user = SubFactory(UserFactory, role=User.Role.CLIENT)
    hotel = SubFactory(HotelFactory)
    booking = None  # Optionnel, sera défini si besoin
    rating = Faker("random_int", min=1, max=5)
    comment = Faker("paragraph", nb_sentences=2, locale="fr_FR")


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class NotificationFactory(DjangoModelFactory):
    """Factory pour Notification."""

    class Meta:
        model = Notification
        skip_postgeneration_save = True

    user = SubFactory(UserFactory)
    type = Notification.Type.INFO
    title = Faker("sentence", nb_words=4, locale="fr_FR")
    message = Faker("paragraph", nb_sentences=2, locale="fr_FR")
    link = ""
    is_read = False