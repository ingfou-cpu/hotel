"""Tests d'infrastructure : vérifie que pytest, factories et Django fonctionnent."""

import pytest
from decimal import Decimal
from django.core.management import call_command
from io import StringIO

from apps.factories import (
    UserFactory,
    HotelFactory,
    RoomFactory,
    AmenityFactory,
    BookingFactory,
    PaymentFactory,
    ReviewFactory,
    NotificationFactory,
)


@pytest.mark.django_db
class TestSystemCheck:
    """Vérifie que le système Django passe les checks."""

    def test_django_check_passes(self):
        """Equivalent à `manage.py check`."""
        out = StringIO()
        call_command("check", stdout=out)
        output = out.getvalue()
        assert "System check identified no issues" in output or "0 issues" in output.lower()


@pytest.mark.django_db
class TestFactoriesBuildValidObjects:
    """Vérifie que les factories créent des objets valides en base."""

    def test_user_factory_creates_client(self):
        user = UserFactory.create_client()
        assert user.email.endswith("@example.com")
        assert user.role == "client"
        assert user.check_password("testpass123")
        assert user.is_active is True

    def test_user_factory_creates_hotel_manager(self):
        user = UserFactory.create_hotel_manager()
        assert user.role == "hotel_manager"

    def test_user_factory_creates_admin(self):
        user = UserFactory.create_admin()
        assert user.role == "admin"
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_amenity_factory(self):
        amenity = AmenityFactory.create(name="Wi-Fi")
        assert amenity.name == "Wi-Fi"
        assert amenity.slug == "amenity-wi-fi"
        # Test unicité
        amenity2 = AmenityFactory.build(name="Wi-Fi")
        assert amenity2.name == "Wi-Fi"

    def test_hotel_factory(self):
        hotel = HotelFactory.create()
        assert hotel.name.startswith("Hôtel")
        assert hotel.city
        assert hotel.country == "France"
        assert 1 <= hotel.stars <= 5
        assert hotel.is_active is True
        assert hotel.manager.role == "hotel_manager"
        # Vérifie les amenities créées automatiquement
        assert hotel.amenities.count() >= 2

    def test_room_factory(self):
        room = RoomFactory.create()
        assert room.hotel is not None
        assert room.room_number.isdigit()
        assert room.room_type in dict(RoomFactory._meta.model.Type.choices).keys()
        assert room.price_per_night >= 0
        assert room.max_occupancy >= 1
        assert room.beds >= 1
        assert room.is_available is True
        assert room.is_active is True
        # Vérifie amenities
        assert room.amenities.count() >= 1

    def test_booking_factory(self):
        booking = BookingFactory.create()
        assert booking.booking_code
        assert len(booking.booking_code) == 10
        assert booking.user.role == "client"
        assert booking.hotel == booking.room.hotel
        assert booking.check_out > booking.check_in
        assert booking.nights == (booking.check_out - booking.check_in).days
        assert booking.adults >= 1
        assert booking.price_per_night == booking.room.price_per_night
        assert booking.total_price > 0
        assert booking.status == "pending"

    def test_payment_factory(self):
        payment = PaymentFactory.create()
        assert payment.booking is not None
        assert payment.user == payment.booking.user
        assert payment.amount == payment.booking.total_price
        assert payment.currency == "eur"
        assert payment.status == "pending"
        assert payment.stripe_session_id.startswith("cs_test_")
        assert payment.stripe_payment_intent_id.startswith("pi_test_")

    def test_review_factory(self):
        review = ReviewFactory.create()
        assert review.user.role == "client"
        assert review.hotel is not None
        assert 1 <= review.rating <= 5
        assert review.comment

    def test_notification_factory(self):
        notif = NotificationFactory.create()
        assert notif.user is not None
        assert notif.type in dict(NotificationFactory._meta.model.Type.choices).keys()
        assert notif.title
        assert notif.message
        assert notif.is_read is False


@pytest.mark.django_db
class TestFactoryRoundTrip:
    """Vérifie le round-trip DB : create -> save -> reload."""

    def test_hotel_room_round_trip(self):
        hotel = HotelFactory.create(name="Hôtel Test Roundtrip")
        room = RoomFactory.create(hotel=hotel, room_number="42", price_per_night=Decimal("150.00"))

        # Recharge depuis la base
        hotel_reloaded = hotel.__class__.objects.get(pk=hotel.pk)
        room_reloaded = room.__class__.objects.get(pk=room.pk)

        assert hotel_reloaded.name == "Hôtel Test Roundtrip"
        assert hotel_reloaded.city == hotel.city
        assert room_reloaded.room_number == "42"
        assert room_reloaded.price_per_night == Decimal("150.00")
        assert room_reloaded.hotel_id == hotel.pk

    def test_booking_calculations_persist(self):
        from datetime import date
        from apps.bookings.models import Booking
        check_in = date(2026, 10, 1)
        check_out = date(2026, 10, 5)  # 4 nuits
        booking = BookingFactory.create(
            price_per_night=Decimal("200.00"),
            check_in=check_in,
            check_out=check_out,
        )
        # Recharge
        booking_reloaded = Booking.objects.get(pk=booking.pk)
        assert booking_reloaded.nights == 4
        assert booking_reloaded.price_per_night == Decimal("200.00")
        # total = 4 * 200 + tax (10%) + service_fee (5) = 800 + 80 + 5 = 885
        assert booking_reloaded.total_price == Decimal("885.00")

    def test_user_role_properties(self):
        client = UserFactory.create_client()
        manager = UserFactory.create_hotel_manager()
        admin = UserFactory.create_admin()

        assert client.is_client is True
        assert client.is_hotel_manager is False
        assert client.is_administrator is False

        assert manager.is_client is False
        assert manager.is_hotel_manager is True
        assert manager.is_administrator is False

        assert admin.is_client is False
        assert admin.is_hotel_manager is False
        assert admin.is_administrator is True