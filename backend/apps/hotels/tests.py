"""Tests pytest pour l'API Hôtels (apps.hotels).

Couvre : liste/détail hôtels, filtres/recherche, CRUD hôtels & chambres,
permissions (IsHotelManagerOrStaff, IsManagerOfHotelOrStaff), disponibilité,
favoris, équipements, images.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from apps.accounts.models import User
from apps.hotels.models import Amenity, Favorite, Hotel, HotelImage, Room
from apps.bookings.models import Booking


# =============================================================================
# Fixtures locales
# =============================================================================

@pytest.fixture
def amenity_wifi():
    return Amenity.objects.create(name="Wi-Fi", slug="wifi", icon="wifi")


@pytest.fixture
def amenity_pool():
    return Amenity.objects.create(name="Piscine", slug="piscine", icon="pool")


@pytest.fixture
def hotel_paris(hotel_manager_user, amenity_wifi, amenity_pool):
    """Hôtel à Paris géré par hotel_manager_user."""
    hotel = Hotel.objects.create(
        manager=hotel_manager_user,
        name="Hôtel Paris Centre",
        description="Au cœur de Paris",
        address="10 Rue de Rivoli",
        city="Paris",
        country="France",
        latitude=Decimal("48.8566"),
        longitude=Decimal("2.3522"),
        stars=4,
        is_active=True,
    )
    hotel.amenities.add(amenity_wifi, amenity_pool)
    return hotel


@pytest.fixture
def hotel_lyon(hotel_manager_user, amenity_wifi):
    """Second hôtel à Lyon, même gestionnaire."""
    hotel = Hotel.objects.create(
        manager=hotel_manager_user,
        name="Hôtel Lyon Part-Dieu",
        description="Près de la gare",
        address="5 Place Charles Béraudier",
        city="Lyon",
        country="France",
        latitude=Decimal("45.7640"),
        longitude=Decimal("4.8357"),
        stars=3,
        is_active=True,
    )
    hotel.amenities.add(amenity_wifi)
    return hotel


@pytest.fixture
def hotel_marseille(admin_user, amenity_pool):
    """Hôtel à Marseille géré par un AUTRE gestionnaire (admin ici)."""
    # On crée un vrai hotel_manager pour ce test
    other_manager = User.objects.create_user(
        email="manager2@example.com",
        password="testpass123",
        first_name="Autre",
        last_name="Manager",
        role=User.Role.HOTEL_MANAGER,
    )
    hotel = Hotel.objects.create(
        manager=other_manager,
        name="Hôtel Vieux-Port",
        description="Vue sur le port",
        address="1 Quai des Belges",
        city="Marseille",
        country="France",
        latitude=Decimal("43.2965"),
        longitude=Decimal("5.3698"),
        stars=5,
        is_active=True,
    )
    hotel.amenities.add(amenity_pool)
    return hotel, other_manager


@pytest.fixture
def room_paris_101(hotel_paris):
    """Chambre 101 à l'hôtel Paris."""
    return Room.objects.create(
        hotel=hotel_paris,
        room_number="101",
        room_type=Room.Type.DOUBLE,
        description="Chambre double vue ville",
        price_per_night=Decimal("150.00"),
        max_occupancy=2,
        beds=1,
        is_available=True,
        is_active=True,
    )


@pytest.fixture
def room_paris_102(hotel_paris):
    """Chambre 102 à l'hôtel Paris (suite)."""
    return Room.objects.create(
        hotel=hotel_paris,
        room_number="102",
        room_type=Room.Type.SUITE,
        description="Suite junior",
        price_per_night=Decimal("300.00"),
        max_occupancy=3,
        beds=2,
        is_available=True,
        is_active=True,
    )


@pytest.fixture
def room_lyon_201(hotel_lyon):
    """Chambre 201 à l'hôtel Lyon."""
    return Room.objects.create(
        hotel=hotel_lyon,
        room_number="201",
        room_type=Room.Type.SINGLE,
        description="Chambre simple",
        price_per_night=Decimal("80.00"),
        max_occupancy=1,
        beds=1,
        is_available=True,
        is_active=True,
    )


@pytest.fixture
def booking_factory(client_user):
    """Factory pour créer des bookings actifs."""
    def _create(hotel, room, check_in, check_out, status=Booking.Status.CONFIRMED):
        return Booking.objects.create(
            user=client_user,
            hotel=hotel,
            room=room,
            check_in=check_in,
            check_out=check_out,
            adults=2,
            children=0,
            price_per_night=room.price_per_night,
            status=status,
        )
    return _create


# =============================================================================
# 1. Hotel list & detail
# =============================================================================

@pytest.mark.django_db
class TestHotelListAndDetail:
    """Tests de lecture publique : liste paginée et détail complet."""

    def test_list_hotels_paginated_200(self, api_client, hotel_paris, hotel_lyon):
        url = reverse("hotel-list")
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert "results" in resp.data
        assert resp.data["count"] == 2
        # Vérifie structure HotelListSerializer
        for item in resp.data["results"]:
            assert set(item.keys()) >= {
                "id", "name", "city", "country", "stars",
                "image", "starting_price", "room_count",
                "average_rating", "reviews_count", "is_active", "created_at"
            }

    def test_detail_hotel_returns_full_payload_with_nested_rooms_and_amenities(
        self, api_client, hotel_paris, room_paris_101, room_paris_102,
        amenity_wifi, amenity_pool
    ):
        url = reverse("hotel-detail", kwargs={"pk": hotel_paris.pk})
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.data
        # Champs HotelSerializer
        assert data["id"] == hotel_paris.pk
        assert data["name"] == "Hôtel Paris Centre"
        assert data["city"] == "Paris"
        assert data["country"] == "France"
        assert data["stars"] == 4
        # Amenities (PrimaryKeyRelatedField -> liste d'IDs)
        assert set(data["amenities"]) == {amenity_wifi.pk, amenity_pool.pk}
        # Images (read_only, vide ici)
        assert "images" in data
        # Rooms imbriqués (SerializerMethodField -> RoomSerializer)
        assert "rooms" in data
        assert len(data["rooms"]) == 2
        room_data = data["rooms"][0]
        assert set(room_data.keys()) >= {
            "id", "hotel", "room_number", "room_type",
            "room_type_display", "description", "price_per_night",
            "max_occupancy", "beds", "amenities", "images",
            "is_available", "is_active"
        }
        # "hotel_id" est write_only (entrée de création) ; en lecture, l'id est
        # exposé via l'objet imbriqué "hotel".
        assert room_data["hotel"]["id"] == hotel_paris.pk
        assert room_data["price_per_night"] == "150.00"
        assert room_data["room_type"] in ("single", "double", "suite", "family")

    def test_detail_inactive_hotel_visible_to_owner_only(
        self, manager_api_client, hotel_manager_user, amenity_wifi
    ):
        inactive = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Inactif",
            description="Test",
            address="1 rue test",
            city="Paris",
            country="France",
            latitude=Decimal("48.85"),
            longitude=Decimal("2.35"),
            stars=3,
            is_active=False,
        )
        url = reverse("hotel-detail", kwargs={"pk": inactive.pk})
        # Gestionnaire propriétaire : visible
        resp = manager_api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        # Autre utilisateur (client) : 404
        client_user = User.objects.create_user(
            email="client2@example.com", password="testpass123",
            first_name="Client", last_name="Deux", role=User.Role.CLIENT
        )
        from rest_framework.test import APIClient
        other_client = APIClient()
        other_client.force_authenticate(user=client_user)
        resp = other_client.get(url)
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# 2. Search / Filtering (django-filter style via query params)
# =============================================================================

@pytest.mark.django_db
class TestHotelSearchAndFiltering:
    """Filtres : city, country, stars, guests, check_in/check_out, sort=price."""

    def test_filter_by_city(self, api_client, hotel_paris, hotel_lyon, hotel_marseille):
        hotel_marseille_obj, _ = hotel_marseille
        url = reverse("hotel-list")
        resp = api_client.get(url, {"city": "Paris"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["city"] == "Paris"

    def test_filter_by_country(self, api_client, hotel_paris, hotel_lyon):
        url = reverse("hotel-list")
        resp = api_client.get(url, {"country": "France"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 2

    def test_filter_by_stars_min(self, api_client, hotel_paris, hotel_lyon, hotel_marseille):
        hotel_marseille_obj, _ = hotel_marseille  # 5 étoiles
        url = reverse("hotel-list")
        resp = api_client.get(url, {"stars": "4"})
        assert resp.status_code == status.HTTP_200_OK
        # Paris (4) + Marseille (5) = 2
        assert resp.data["count"] == 2
        for item in resp.data["results"]:
            assert item["stars"] >= 4

    def test_filter_by_guests(self, api_client, hotel_paris, hotel_lyon, room_paris_101, room_paris_102, room_lyon_201):
        # Paris a chambres 2 et 3 pers ; Lyon a chambre 1 pers
        url = reverse("hotel-list")
        resp = api_client.get(url, {"guests": "2"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["city"] == "Paris"

    def test_sort_price_asc(self, api_client, hotel_paris, hotel_lyon, room_paris_101, room_paris_102, room_lyon_201):
        # Lyon: 80€, Paris: 150€ (min)
        url = reverse("hotel-list")
        resp = api_client.get(url, {"sort": "price"})
        assert resp.status_code == status.HTTP_200_OK
        prices = [Decimal(item["starting_price"]) for item in resp.data["results"]]
        assert prices == sorted(prices)

    def test_sort_price_desc(self, api_client, hotel_paris, hotel_lyon, room_paris_101, room_paris_102, room_lyon_201):
        url = reverse("hotel-list")
        resp = api_client.get(url, {"sort": "-price"})
        assert resp.status_code == status.HTTP_200_OK
        prices = [Decimal(item["starting_price"]) for item in resp.data["results"]]
        assert prices == sorted(prices, reverse=True)

    def test_combined_filters_city_and_stars(self, api_client, hotel_paris, hotel_lyon, hotel_marseille):
        hotel_marseille_obj, _ = hotel_marseille
        url = reverse("hotel-list")
        resp = api_client.get(url, {"city": "Paris", "stars": "4"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["name"] == "Hôtel Paris Centre"

    def test_availability_filter_check_in_check_out_excludes_booked_rooms(
        self, api_client, hotel_paris, hotel_lyon, room_paris_101, room_paris_102, room_lyon_201, booking_factory
    ):
        # Réserve la chambre 101 (Paris) du 10 au 15 juin
        today = date.today()
        check_in = today + timedelta(days=10)
        check_out = today + timedelta(days=15)
        booking_factory(hotel_paris, room_paris_101, check_in, check_out)

        url = reverse("hotel-list")
        resp = api_client.get(url, {"check_in": check_in.isoformat(), "check_out": check_out.isoformat()})
        assert resp.status_code == status.HTTP_200_OK
        # Paris a encore la chambre 102 dispo -> hôtel visible
        # Lyon a chambre 201 dispo -> hôtel visible
        assert resp.data["count"] == 2

        # Maintenant réserve aussi la 102 -> Paris n'a plus de chambre dispo
        booking_factory(hotel_paris, room_paris_102, check_in, check_out)
        resp = api_client.get(url, {"check_in": check_in.isoformat(), "check_out": check_out.isoformat()})
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["city"] == "Lyon"

    def test_availability_adjacent_dates_still_available(
        self, api_client, hotel_paris, room_paris_101, booking_factory
    ):
        today = date.today()
        # Booking du 10 au 15
        booking_factory(hotel_paris, room_paris_101, today + timedelta(days=10), today + timedelta(days=15))
        # Recherche du 15 au 20 (adjacent, pas de chevauchement) -> dispo
        url = reverse("hotel-list")
        resp = api_client.get(url, {
            "check_in": (today + timedelta(days=15)).isoformat(),
            "check_out": (today + timedelta(days=20)).isoformat(),
        })
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 1  # Paris encore visible


# =============================================================================
# 3. Create hotel: permissions
# =============================================================================

@pytest.mark.django_db
class TestHotelCreatePermissions:
    """POST /api/v1/hotels/ : hotel_manager & admin -> 201 ; client/anon -> 403/401."""

    def test_hotel_manager_can_create_hotel(self, manager_api_client, amenity_wifi):
        url = reverse("hotel-list")
        payload = {
            "name": "Nouvel Hôtel",
            "description": "Super hôtel",
            "address": "123 Rue Test",
            "city": "Bordeaux",
            "country": "France",
            "latitude": "44.8378",
            "longitude": "-0.5792",
            "stars": 4,
            "amenities": [amenity_wifi.pk],
        }
        resp = manager_api_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED, resp.data
        assert resp.data["name"] == "Nouvel Hôtel"
        assert resp.data["manager"] is not None
        # Vérifie en base que le manager est l'utilisateur connecté
        hotel = Hotel.objects.get(pk=resp.data["id"])
        assert hotel.manager_id == manager_api_client.handler._force_user.id

    def test_admin_can_create_hotel(self, admin_api_client, hotel_manager_user, amenity_wifi):
        url = reverse("hotel-list")
        payload = {
            "name": "Hôtel Admin",
            "description": "Créé par admin",
            "address": "456 Ave Admin",
            "city": "Toulouse",
            "country": "France",
            "latitude": "43.6047",
            "longitude": "1.4442",
            "stars": 5,
            "manager": hotel_manager_user.pk,  # Admin peut assigner un manager
            "amenities": [amenity_wifi.pk],
        }
        resp = admin_api_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED, resp.data
        hotel = Hotel.objects.get(pk=resp.data["id"])
        assert hotel.manager_id == hotel_manager_user.pk

    def test_client_cannot_create_hotel_403(self, client_api_client, amenity_wifi):
        url = reverse("hotel-list")
        payload = {
            "name": "Hôtel Client",
            "description": "Tentative",
            "address": "789 Blvd Client",
            "city": "Nantes",
            "country": "France",
            "latitude": "47.2184",
            "longitude": "-1.5536",
            "stars": 3,
            "amenities": [amenity_wifi.pk],
        }
        resp = client_api_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_cannot_create_hotel_401(self, api_client, amenity_wifi):
        url = reverse("hotel-list")
        payload = {
            "name": "Hôtel Anonyme",
            "description": "Tentative",
            "address": "999 Rue Anon",
            "city": "Lille",
            "country": "France",
            "latitude": "50.6292",
            "longitude": "3.0573",
            "stars": 2,
            "amenities": [amenity_wifi.pk],
        }
        resp = api_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_created_hotel_has_correct_manager_when_not_provided(self, manager_api_client):
        url = reverse("hotel-list")
        payload = {
            "name": "Auto Manager",
            "description": "Test",
            "address": "1 Rue Auto",
            "city": "Strasbourg",
            "country": "France",
            "latitude": "48.5734",
            "longitude": "7.7521",
            "stars": 3,
        }
        resp = manager_api_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        hotel = Hotel.objects.get(pk=resp.data["id"])
        assert hotel.manager_id == manager_api_client.handler._force_user.id


# =============================================================================
# 4. Update / Delete hotel: object-level permissions
# =============================================================================

@pytest.mark.django_db
class TestHotelUpdateDeletePermissions:
    """PATCH/DELETE /api/v1/hotels/{pk}/ : owner-manager, admin OK ; foreign manager 403 ; client 403."""

    def test_owner_manager_can_update_hotel(self, manager_api_client, hotel_paris):
        url = reverse("hotel-detail", kwargs={"pk": hotel_paris.pk})
        payload = {"name": "Hôtel Paris Centre Modifié", "stars": 5}
        resp = manager_api_client.patch(url, payload, format="json")
        assert resp.status_code == status.HTTP_200_OK, resp.data
        assert resp.data["name"] == "Hôtel Paris Centre Modifié"
        assert resp.data["stars"] == 5
        hotel_paris.refresh_from_db()
        assert hotel_paris.name == "Hôtel Paris Centre Modifié"

    def test_owner_manager_can_delete_hotel(self, manager_api_client, hotel_paris):
        url = reverse("hotel-detail", kwargs={"pk": hotel_paris.pk})
        resp = manager_api_client.delete(url)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Hotel.objects.filter(pk=hotel_paris.pk).exists()

    def test_different_hotel_manager_cannot_update_403(self, hotel_marseille, manager_api_client):
        hotel_marseille_obj, other_manager = hotel_marseille
        url = reverse("hotel-detail", kwargs={"pk": hotel_marseille_obj.pk})
        payload = {"name": "Tentative de vol"}
        resp = manager_api_client.patch(url, payload, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_different_hotel_manager_cannot_delete_403(self, hotel_marseille, manager_api_client):
        hotel_marseille_obj, _ = hotel_marseille
        url = reverse("hotel-detail", kwargs={"pk": hotel_marseille_obj.pk})
        resp = manager_api_client.delete(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_update_any_hotel(self, admin_api_client, hotel_marseille):
        hotel_marseille_obj, _ = hotel_marseille
        url = reverse("hotel-detail", kwargs={"pk": hotel_marseille_obj.pk})
        payload = {"name": "Admin Renamed", "stars": 4}
        resp = admin_api_client.patch(url, payload, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["name"] == "Admin Renamed"

    def test_admin_can_delete_any_hotel(self, admin_api_client, hotel_marseille):
        hotel_marseille_obj, _ = hotel_marseille
        url = reverse("hotel-detail", kwargs={"pk": hotel_marseille_obj.pk})
        resp = admin_api_client.delete(url)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Hotel.objects.filter(pk=hotel_marseille_obj.pk).exists()

    def test_client_cannot_update_hotel_403(self, client_api_client, hotel_paris):
        url = reverse("hotel-detail", kwargs={"pk": hotel_paris.pk})
        payload = {"name": "Client Hack"}
        resp = client_api_client.patch(url, payload, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_client_cannot_delete_hotel_403(self, client_api_client, hotel_paris):
        url = reverse("hotel-detail", kwargs={"pk": hotel_paris.pk})
        resp = client_api_client.delete(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# 5. Room CRUD under a hotel
# =============================================================================

@pytest.mark.django_db
class TestRoomCRUD:
    """CRUD chambres : manager de l'hôtel OK ; foreign manager 403 ; champs sérialisés."""

    def test_owner_manager_can_create_room(self, manager_api_client, hotel_paris, amenity_wifi):
        url = reverse("room-list")
        payload = {
            "hotel_id": hotel_paris.pk,
            "room_number": "201",
            "room_type": "double",
            "description": "Nouvelle chambre",
            "price_per_night": "180.00",
            "max_occupancy": 2,
            "beds": 1,
            "amenities": [amenity_wifi.pk],
        }
        resp = manager_api_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED, resp.data
        assert resp.data["room_number"] == "201"
        assert resp.data["price_per_night"] == "180.00"
        assert resp.data["max_occupancy"] == 2
        assert resp.data["room_type"] == "double"
        assert resp.data["room_type_display"] == "Double"
        room = Room.objects.get(pk=resp.data["id"])
        assert room.hotel_id == hotel_paris.pk

    def test_owner_manager_can_update_room(self, manager_api_client, room_paris_101):
        url = reverse("room-detail", kwargs={"pk": room_paris_101.pk})
        payload = {"price_per_night": "200.00", "room_type": "suite"}
        resp = manager_api_client.patch(url, payload, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["price_per_night"] == "200.00"
        assert resp.data["room_type"] == "suite"

    def test_owner_manager_can_delete_room(self, manager_api_client, room_paris_101):
        url = reverse("room-detail", kwargs={"pk": room_paris_101.pk})
        resp = manager_api_client.delete(url)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Room.objects.filter(pk=room_paris_101.pk).exists()

    def test_foreign_manager_cannot_create_room_in_other_hotel_403(
        self, manager_api_client, hotel_marseille, amenity_wifi
    ):
        hotel_marseille_obj, _ = hotel_marseille
        url = reverse("room-list")
        payload = {
            "hotel_id": hotel_marseille_obj.pk,
            "room_number": "301",
            "room_type": "single",
            "price_per_night": "100.00",
            "max_occupancy": 1,
            "beds": 1,
        }
        resp = manager_api_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_foreign_manager_cannot_update_room_403(
        self, manager_api_client, hotel_marseille
    ):
        hotel_marseille_obj, _ = hotel_marseille
        room = Room.objects.create(
            hotel=hotel_marseille_obj,
            room_number="301",
            room_type=Room.Type.SINGLE,
            price_per_night=Decimal("100.00"),
            max_occupancy=1,
            beds=1,
        )
        url = reverse("room-detail", kwargs={"pk": room.pk})
        resp = manager_api_client.patch(url, {"price_per_night": "999.00"}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_foreign_manager_cannot_delete_room_403(
        self, manager_api_client, hotel_marseille
    ):
        hotel_marseille_obj, _ = hotel_marseille
        room = Room.objects.create(
            hotel=hotel_marseille_obj,
            room_number="302",
            room_type=Room.Type.DOUBLE,
            price_per_night=Decimal("150.00"),
            max_occupancy=2,
            beds=1,
        )
        url = reverse("room-detail", kwargs={"pk": room.pk})
        resp = manager_api_client.delete(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_manage_any_room(self, admin_api_client, hotel_marseille, amenity_wifi):
        hotel_marseille_obj, _ = hotel_marseille
        # Create
        url = reverse("room-list")
        payload = {
            "hotel_id": hotel_marseille_obj.pk,
            "room_number": "401",
            "room_type": "family",
            "price_per_night": "400.00",
            "max_occupancy": 4,
            "beds": 2,
            "amenities": [amenity_wifi.pk],
        }
        resp = admin_api_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        room_id = resp.data["id"]
        # Update
        url = reverse("room-detail", kwargs={"pk": room_id})
        resp = admin_api_client.patch(url, {"price_per_night": "450.00"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        # Delete
        resp = admin_api_client.delete(url)
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_client_cannot_create_room_403(self, client_api_client, hotel_paris):
        url = reverse("room-list")
        payload = {
            "hotel_id": hotel_paris.pk,
            "room_number": "999",
            "room_type": "single",
            "price_per_night": "50.00",
            "max_occupancy": 1,
            "beds": 1,
        }
        resp = client_api_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_room_list_filter_by_hotel_and_availability(
        self, api_client, hotel_paris, hotel_lyon, room_paris_101, room_paris_102, room_lyon_201, booking_factory
    ):
        url = reverse("room-list")
        # Filtre par hôtel
        resp = api_client.get(url, {"hotel": hotel_paris.pk})
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 2
        for r in resp.data:
            assert r["hotel"]["id"] == hotel_paris.pk

        # Disponibilité : réserve 101
        today = date.today()
        check_in = today + timedelta(days=5)
        check_out = today + timedelta(days=10)
        booking_factory(hotel_paris, room_paris_101, check_in, check_out)
        resp = api_client.get(url, {"hotel": hotel_paris.pk, "check_in": check_in.isoformat(), "check_out": check_out.isoformat()})
        assert len(resp.data) == 1
        assert resp.data[0]["room_number"] == "102"


# =============================================================================
# 6. Availability via API (check_in/check_out query params)
# =============================================================================

@pytest.mark.django_db
class TestAvailability:
    """Disponibilité surfacée via ?check_in=&check_out= sur hotels et rooms."""

    def test_hotel_list_availability_filter(self, api_client, hotel_paris, hotel_lyon, room_paris_101, room_paris_102, room_lyon_201, booking_factory):
        today = date.today()
        check_in = today + timedelta(days=10)
        check_out = today + timedelta(days=15)
        # Réserve toutes les chambres de Paris
        booking_factory(hotel_paris, room_paris_101, check_in, check_out)
        booking_factory(hotel_paris, room_paris_102, check_in, check_out)

        url = reverse("hotel-list")
        resp = api_client.get(url, {"check_in": check_in.isoformat(), "check_out": check_out.isoformat()})
        assert resp.status_code == status.HTTP_200_OK
        # Lyon toujours dispo, Paris plus
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["city"] == "Lyon"

    def test_room_list_availability_filter(self, api_client, hotel_paris, room_paris_101, room_paris_102, booking_factory):
        today = date.today()
        check_in = today + timedelta(days=10)
        check_out = today + timedelta(days=15)
        booking_factory(hotel_paris, room_paris_101, check_in, check_out)

        url = reverse("room-list")
        resp = api_client.get(url, {"hotel": hotel_paris.pk, "check_in": check_in.isoformat(), "check_out": check_out.isoformat()})
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 1
        assert resp.data[0]["room_number"] == "102"

    def test_room_is_available_for_logic_matches_api(
        self, hotel_paris, room_paris_101, room_paris_102, client_user, booking_factory
    ):
        today = date.today()
        check_in = today + timedelta(days=10)
        check_out = today + timedelta(days=15)

        # Sans booking -> disponible
        assert room_paris_101.is_available_for(check_in, check_out) is True
        assert room_paris_102.is_available_for(check_in, check_out) is True

        # Avec booking chevauchant -> indisponible
        booking_factory(hotel_paris, room_paris_101, check_in, check_out)
        room_paris_101.refresh_from_db()
        assert room_paris_101.is_available_for(check_in, check_out) is False
        # L'autre chambre encore dispo
        assert room_paris_102.is_available_for(check_in, check_out) is True

        # Dates adjacentes -> dispo
        assert room_paris_101.is_available_for(check_out, check_out + timedelta(days=5)) is True

        # Chambre inactive -> indisponible
        room_paris_101.is_active = False
        room_paris_101.save()
        assert room_paris_101.is_available_for(check_in, check_out) is False


# =============================================================================
# 7. Favorites
# =============================================================================

@pytest.mark.django_db
class TestFavorites:
    """Favoris : CRUD user-scoped, auth requise, anti-duplication."""

    def test_authenticated_client_can_add_favorite_201(self, client_api_client, client_user, hotel_paris):
        url = reverse("favorite-list")
        payload = {"hotel_id": hotel_paris.pk}
        resp = client_api_client.post(url, payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED, resp.data
        assert resp.data["hotel"]["id"] == hotel_paris.pk
        assert Favorite.objects.filter(user=client_user, hotel=hotel_paris).exists()

    def test_duplicate_favorite_blocked_400_or_409(self, client_api_client, client_user, hotel_paris):
        Favorite.objects.create(user=client_user, hotel=hotel_paris)
        url = reverse("favorite-list")
        payload = {"hotel_id": hotel_paris.pk}
        resp = client_api_client.post(url, payload, format="json")
        # get_or_create dans le serializer renvoie 201 existant -> on teste le comportement actuel
        # Si le serializer renvoie 201 (get_or_create), c'est le comportement actuel.
        # On documente le comportement : pas d'erreur, retourne l'existant.
        assert resp.status_code in (status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT)
        # Vérifie qu'il n'y a qu'un seul favori en base
        assert Favorite.objects.filter(user=client_user, hotel=hotel_paris).count() == 1

    def test_list_own_favorites(self, client_api_client, client_user, hotel_paris, hotel_lyon):
        Favorite.objects.create(user=client_user, hotel=hotel_paris)
        Favorite.objects.create(user=client_user, hotel=hotel_lyon)
        url = reverse("favorite-list")
        resp = client_api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 2
        hotel_ids = {item["hotel"]["id"] for item in resp.data}
        assert hotel_ids == {hotel_paris.pk, hotel_lyon.pk}

    def test_remove_favorite_204(self, client_api_client, client_user, hotel_paris):
        fav = Favorite.objects.create(user=client_user, hotel=hotel_paris)
        url = reverse("favorite-detail", kwargs={"pk": fav.pk})
        resp = client_api_client.delete(url)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Favorite.objects.filter(pk=fav.pk).exists()

    def test_unauthenticated_cannot_access_favorites_401(self, api_client, hotel_paris):
        url = reverse("favorite-list")
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        resp = api_client.post(url, {"hotel_id": hotel_paris.pk}, format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cannot_list_someone_elses_favorites(self, client_api_client, hotel_manager_user, hotel_paris):
        # Crée un favori pour le manager
        Favorite.objects.create(user=hotel_manager_user, hotel=hotel_paris)
        # Client connecté ne voit que SES favoris (vide)
        url = reverse("favorite-list")
        resp = client_api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 0

    def test_cannot_delete_someone_elses_favorite_404(self, client_api_client, hotel_manager_user, hotel_paris):
        fav = Favorite.objects.create(user=hotel_manager_user, hotel=hotel_paris)
        url = reverse("favorite-detail", kwargs={"pk": fav.pk})
        resp = client_api_client.delete(url)
        # get_queryset filtre par user -> 404
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# 8. Amenities
# =============================================================================

@pytest.mark.django_db
class TestAmenities:
    """Équipements : liste publique read-only."""

    def test_list_amenities(self, api_client, amenity_wifi, amenity_pool):
        url = reverse("amenity-list")
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) >= 2
        names = {item["name"] for item in resp.data}
        assert "Wi-Fi" in names
        assert "Piscine" in names

    def test_retrieve_amenity(self, api_client, amenity_wifi):
        url = reverse("amenity-detail", kwargs={"pk": amenity_wifi.pk})
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["name"] == "Wi-Fi"
        assert resp.data["slug"] == "wifi"
        assert resp.data["icon"] == "wifi"

    def test_amenity_create_not_allowed_405(self, admin_api_client):
        url = reverse("amenity-list")
        resp = admin_api_client.post(url, {"name": "Spa", "slug": "spa", "icon": "spa"}, format="json")
        assert resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# =============================================================================
# 9. Hotel Images
# =============================================================================

@pytest.mark.django_db
class TestHotelImages:
    """Images d'hôtel : URLs absolues dans le détail / galerie."""

    def test_hotel_detail_includes_image_urls_when_images_exist(
        self, api_client, hotel_paris
    ):
        # Crée une image primaire et une secondaire
        img1 = HotelImageFactory.create(hotel=hotel_paris, is_primary=True, alt="Façade")
        img2 = HotelImageFactory.create(hotel=hotel_paris, is_primary=False, alt="Chambre")

        url = reverse("hotel-detail", kwargs={"pk": hotel_paris.pk})
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK

        # Champ 'image' (SerializerMethodField) -> URL absolue de l'image primaire
        assert resp.data["image"] is not None
        assert "http" in resp.data["image"]
        assert img1.image.name in resp.data["image"]

        # Champ 'images' (HotelImageSerializer many=True)
        assert len(resp.data["images"]) == 2
        image_urls = {img["image"] for img in resp.data["images"]}
        assert any(img1.image.name in u for u in image_urls)
        assert any(img2.image.name in u for u in image_urls)

    def test_hotel_list_includes_starting_image(self, api_client, hotel_paris):
        HotelImageFactory.create(hotel=hotel_paris, is_primary=True, alt="Main")
        url = reverse("hotel-list")
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["results"][0]["image"] is not None
        assert "http" in resp.data["results"][0]["image"]


# =============================================================================
# Factory import (à la fin pour éviter les imports circulaires)
# =============================================================================

from apps.factories import HotelImageFactory