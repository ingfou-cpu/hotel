"""Tests complets pour l'API des réservations (apps.bookings).

Couvre :
- Création (auth, anonymes, snapshot prix)
- Validation dates (ordre, passé)
- Anti-double-réservation (chevauchement, adjacence)
- Code de réservation (unicité, format)
- Cycle de vie (transitions valides/invalides)
- Règle délai annulation
- Visibilité par rôle (client, gestionnaire)
- Filtrage par statut
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status

from apps.bookings.models import Booking
from apps.hotels.models import Hotel, Room
from apps.accounts.models import User


# ---------------------------------------------------------------------------
# Helpers locaux
# ---------------------------------------------------------------------------

def _today():
    """Date du jour selon le fuseau horaire Django (timezone.localdate)."""
    return timezone.localdate()


def _future_dates(days_ahead=5, nights=3):
    """Retourne (check_in, check_out) futurs."""
    check_in = _today() + timedelta(days=days_ahead)
    check_out = check_in + timedelta(days=nights)
    return check_in, check_out


def _past_dates(nights=3):
    """Retourne (check_in, check_out) dans le passé."""
    check_in = _today() - timedelta(days=10)
    check_out = check_in + timedelta(days=nights)
    return check_in, check_out


# ---------------------------------------------------------------------------
# 1. Création de réservation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBookingCreate:
    """Tests de création POST /api/v1/bookings/."""

    def test_create_authenticated_client_returns_201(self, client_api_client, room):
        """Client authentifié → 201 Created."""
        check_in, check_out = _future_dates()
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
            "children": 0,
        }
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert "booking_code" in resp.data
        assert resp.data["status"] == Booking.Status.PENDING
        assert "total_price" in resp.data
        assert "id" in resp.data

    def test_create_anonymous_returns_401(self, api_client, room):
        """Requête anonyme → 401 Unauthorized."""
        check_in, check_out = _future_dates()
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = api_client.post("/api/v1/bookings/", payload, format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_price_snapshot_frozen_at_creation(
        self, client_api_client, hotel_manager_user, room
    ):
        """Le total_price est figé au moment de la création (snapshot prix)."""
        check_in, check_out = _future_dates()
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        # Création réservation
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        booking_id = resp.data["id"]
        original_total = Decimal(str(resp.data["total_price"]))
        original_price_per_night = Decimal(str(resp.data.get("price_per_night", room.price_per_night)))

        # Modifier le prix de la chambre APRÈS la réservation
        room.price_per_night = Decimal("200.00")
        room.save()

        # Récupérer la réservation : le total ne doit pas avoir changé
        resp_get = client_api_client.get(f"/api/v1/bookings/{booking_id}/")
        assert resp_get.status_code == status.HTTP_200_OK
        current_total = Decimal(str(resp_get.data["total_price"]))
        current_price_per_night = Decimal(str(resp_get.data["price_per_night"]))

        assert current_total == original_total, (
            "Le total_price doit rester figé (snapshot) après modification du prix chambre"
        )
        assert current_price_per_night == original_price_per_night, (
            "price_per_night doit être le snapshot au moment de la réservation"
        )

    def test_total_price_calculation_matches_settings(self, client_api_client, room):
        """total_price = (price_per_night * nights) + tax(10%) + service_fee(5.0)."""
        check_in, check_out = _future_dates(nights=4)
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        booking_id = resp.data["id"]

        # Récupérer via GET pour avoir le serializer complet (avec tax_amount, service_fee)
        resp_get = client_api_client.get(f"/api/v1/bookings/{booking_id}/")
        assert resp_get.status_code == status.HTTP_200_OK

        price_per_night = Decimal(str(room.price_per_night))  # 120.00
        nights = 4
        subtotal = price_per_night * nights  # 480.00
        tax_rate = Decimal(str(settings.BOOKING_TAX_RATE))  # 0.10
        service_fee = Decimal(str(settings.BOOKING_SERVICE_FEE))  # 5.0
        expected_tax = round(subtotal * tax_rate, 2)  # 48.00
        expected_total = round(subtotal + expected_tax + service_fee, 2)  # 533.00

        actual_total = Decimal(str(resp_get.data["total_price"]))
        actual_tax = Decimal(str(resp_get.data["tax_amount"]))
        actual_service_fee = Decimal(str(resp_get.data["service_fee"]))

        assert actual_tax == expected_tax
        assert actual_service_fee == service_fee
        assert actual_total == expected_total


# ---------------------------------------------------------------------------
# 2. Validation des dates
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBookingDateValidation:
    """Tests de validation des dates (check_in < check_out, pas dans le passé)."""

    def test_end_date_before_start_date_returns_400(self, client_api_client, room):
        """check_out <= check_in → 400 Bad Request."""
        check_in = date.today() + timedelta(days=10)
        check_out = check_in  # même jour = invalide
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "check_out" in resp.data

    def test_end_date_before_start_date_reverse_order_returns_400(self, client_api_client, room):
        """check_out < check_in → 400 Bad Request."""
        check_in = date.today() + timedelta(days=10)
        check_out = check_in - timedelta(days=1)
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "check_out" in resp.data

    def test_past_start_date_returns_400(self, client_api_client, room):
        """check_in dans le passé → 400 Bad Request."""
        check_in, check_out = _past_dates()
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "check_in" in resp.data

    def test_today_start_date_allowed(self, client_api_client, room):
        """check_in = aujourd'hui → autorisé (201)."""
        check_in = _today()
        check_out = check_in + timedelta(days=2)
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED


# ---------------------------------------------------------------------------
# 3. Anti-double-réservation (critique)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAntiDoubleBooking:
    """Tests de la contrainte d'exclusion (anti-double-réservation)."""

    def test_overlapping_bookings_same_room_rejected(self, client_api_client, room):
        """Deux réservations chevauchantes pour la MÊME chambre → 400/409."""
        check_in, check_out = _future_dates(days_ahead=5, nights=5)
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }

        # Première réservation → 201
        resp1 = client_api_client.post("/api/v1/bookings/", payload, format="json")
        assert resp1.status_code == status.HTTP_201_CREATED
        booking1_id = resp1.data["id"]

        # Deuxième réservation chevauchante (mêmes dates) → rejet
        resp2 = client_api_client.post("/api/v1/bookings/", payload, format="json")
        assert resp2.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT)
        assert "room" in resp2.data or "non_field_errors" in resp2.data or "detail" in resp2.data

    def test_partially_overlapping_bookings_rejected(self, client_api_client, room):
        """Chevauchement partiel (début avant fin de la 1re) → rejet."""
        check_in1, check_out1 = _future_dates(days_ahead=5, nights=5)  # J5-J10
        payload1 = {
            "room": room.id,
            "check_in": check_in1.isoformat(),
            "check_out": check_out1.isoformat(),
            "adults": 2,
        }
        resp1 = client_api_client.post("/api/v1/bookings/", payload1, format="json")
        assert resp1.status_code == status.HTTP_201_CREATED

        # Deuxième réservation : J8-J12 (chevauche J8-J10)
        check_in2 = check_in1 + timedelta(days=3)
        check_out2 = check_out1 + timedelta(days=2)
        payload2 = {
            "room": room.id,
            "check_in": check_in2.isoformat(),
            "check_out": check_out2.isoformat(),
            "adults": 2,
        }
        resp2 = client_api_client.post("/api/v1/bookings/", payload2, format="json")
        assert resp2.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT)

    def test_adjacent_bookings_same_room_allowed(self, client_api_client, room):
        """Réservations adjacentes (check_out == check_in suivant) → les deux réussissent."""
        check_in1, check_out1 = _future_dates(days_ahead=5, nights=3)  # J5-J8
        payload1 = {
            "room": room.id,
            "check_in": check_in1.isoformat(),
            "check_out": check_out1.isoformat(),
            "adults": 2,
        }
        resp1 = client_api_client.post("/api/v1/bookings/", payload1, format="json")
        assert resp1.status_code == status.HTTP_201_CREATED

        # Deuxième réservation : commence exactement quand la première finit (J8-J11)
        check_in2 = check_out1
        check_out2 = check_in2 + timedelta(days=3)
        payload2 = {
            "room": room.id,
            "check_in": check_in2.isoformat(),
            "check_out": check_out2.isoformat(),
            "adults": 2,
        }
        resp2 = client_api_client.post("/api/v1/bookings/", payload2, format="json")
        assert resp2.status_code == status.HTTP_201_CREATED, (
            f"Réservation adjacente devrait être acceptée. Erreur: {resp2.data}"
        )

    def test_overlapping_different_rooms_allowed(self, client_api_client, hotel):
        """Deux chambres diff. du même hôtel, mêmes dates → autorisées."""
        room1 = RoomFactory.create(hotel=hotel, room_number="101")
        room2 = RoomFactory.create(hotel=hotel, room_number="102")
        check_in, check_out = _future_dates(days_ahead=5, nights=3)

        payload1 = {
            "room": room1.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        payload2 = {
            "room": room2.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }

        resp1 = client_api_client.post("/api/v1/bookings/", payload1, format="json")
        assert resp1.status_code == status.HTTP_201_CREATED

        resp2 = client_api_client.post("/api/v1/bookings/", payload2, format="json")
        assert resp2.status_code == status.HTTP_201_CREATED

    def test_database_exclusion_constraint_enforced(self, room):
        """La contrainte d'exclusion PostgreSQL (GiST) bloque au niveau DB.
        
        Note: SQLite n'a pas de support GiST, ce test vérifie que la validation
        applicative (clean()) bloque bien les chevauchements. Sur PostgreSQL
        avec la migration 0002, la contrainte DB prendrait le relais.
        """
        check_in, check_out = _future_dates(days_ahead=5, nights=3)

        # Première réservation via modèle direct
        booking1 = Booking.objects.create(
            user=UserFactory.create_client(),
            hotel=room.hotel,
            room=room,
            check_in=check_in,
            check_out=check_out,
            adults=2,
            price_per_night=room.price_per_night,
        )

        # Deuxième réservation chevauchante → ValidationError au clean()
        booking2 = Booking(
            user=UserFactory.create_client(),
            hotel=room.hotel,
            room=room,
            check_in=check_in,
            check_out=check_out,
            adults=2,
            price_per_night=room.price_per_night,
        )
        with pytest.raises(ValidationError) as exc:
            booking2.full_clean()
        assert "room" in exc.value.message_dict
        assert "déjà réservée" in exc.value.message_dict["room"][0]


# ---------------------------------------------------------------------------
# 4. Code de réservation auto-généré
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBookingCode:
    """Tests du booking_code (unique, présent, format stable)."""

    def test_booking_code_present_on_create(self, client_api_client, room):
        """booking_code présent dans la réponse de création."""
        check_in, check_out = _future_dates()
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert "booking_code" in resp.data
        assert resp.data["booking_code"]  # non vide

    def test_booking_code_format_10_chars_alphanumeric(self, client_api_client, room):
        """Format : 10 caractères alphanumériques majuscules."""
        check_in, check_out = _future_dates()
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        code = resp.data["booking_code"]
        assert len(code) == 10
        assert code.isalnum()
        assert code.isupper()

    def test_booking_code_unique_across_bookings(self, client_api_client, room):
        """Unicité du code sur plusieurs réservations."""
        codes = set()
        for i in range(5):
            check_in = date.today() + timedelta(days=10 + i * 5)
            check_out = check_in + timedelta(days=2)
            payload = {
                "room": room.id,
                "check_in": check_in.isoformat(),
                "check_out": check_out.isoformat(),
                "adults": 1,
            }
            resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
            assert resp.status_code == status.HTTP_201_CREATED
            codes.add(resp.data["booking_code"])
        assert len(codes) == 5, "Tous les codes doivent être uniques"

    def test_booking_code_immutable_after_creation(self, client_api_client, room):
        """booking_code ne change pas après création."""
        check_in, check_out = _future_dates()
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        code = resp.data["booking_code"]
        booking_id = resp.data["id"]

        # Récupérer plus tard
        resp_get = client_api_client.get(f"/api/v1/bookings/{booking_id}/")
        assert resp_get.data["booking_code"] == code


# ---------------------------------------------------------------------------
# 5. Cycle de vie (transitions de statut)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBookingLifecycle:
    """Tests des transitions de statut valides et invalides."""

    # -- Transitions VALIDES --

    def test_pending_to_confirmed_by_manager(self, manager_api_client, booking):
        """pending → confirmed par gestionnaire → 200."""
        assert booking.status == Booking.Status.PENDING
        resp = manager_api_client.post(f"/api/v1/bookings/{booking.id}/confirm/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == Booking.Status.CONFIRMED
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CONFIRMED

    def test_pending_to_cancelled_by_client_within_deadline(self, client_api_client, booking):
        """pending → cancelled par client (dans délai) → 200."""
        # booking a check_in dans le futur (> 2 jours) → can_cancel() = True
        assert booking.can_cancel() is True
        resp = client_api_client.post(f"/api/v1/bookings/{booking.id}/cancel/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == Booking.Status.CANCELLED
        assert resp.data["cancelled_at"] is not None
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CANCELLED

    def test_confirmed_to_completed_by_manager_after_checkout(self, manager_api_client, booking):
        """confirmed → completed par gestionnaire (après check_out) → 200."""
        # Passer d'abord à confirmed
        booking.confirm()
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CONFIRMED

        # Modifier check_in et check_out pour qu'ils soient dans le passé
        # (check_out doit rester > check_in pour satisfaire la contrainte)
        booking.check_in = date.today() - timedelta(days=3)
        booking.check_out = date.today() - timedelta(days=1)
        booking.save(update_fields=["check_in", "check_out"])

        resp = manager_api_client.post(f"/api/v1/bookings/{booking.id}/complete/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == Booking.Status.COMPLETED
        booking.refresh_from_db()
        assert booking.status == Booking.Status.COMPLETED

    # -- Transitions INVALIDES --

    def test_cancelled_to_confirmed_rejected(self, manager_api_client, booking):
        """cancelled → confirmed → 400."""
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status"])
        resp = manager_api_client.post(f"/api/v1/bookings/{booking.id}/confirm/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in resp.data

    def test_completed_to_cancelled_rejected(self, client_api_client, booking):
        """completed → cancelled → 400."""
        booking.status = Booking.Status.CONFIRMED
        # Mettre les dates dans le passé pour pouvoir compléter
        booking.check_in = date.today() - timedelta(days=3)
        booking.check_out = date.today() - timedelta(days=1)
        booking.save(update_fields=["status", "check_in", "check_out"])
        booking.complete()
        booking.refresh_from_db()
        assert booking.status == Booking.Status.COMPLETED

        resp = client_api_client.post(f"/api/v1/bookings/{booking.id}/cancel/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in resp.data

    def test_confirmed_to_cancelled_after_deadline_rejected(self, client_api_client, booking):
        """confirmed → cancelled APRÈS délai → 400."""
        booking.confirm()
        booking.refresh_from_db()
        # Rapprocher check_in à demain (délai 2 jours dépassé)
        booking.check_in = date.today() + timedelta(days=1)
        booking.save(update_fields=["check_in"])
        assert booking.can_cancel() is False

        resp = client_api_client.post(f"/api/v1/bookings/{booking.id}/cancel/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "délai" in resp.data["detail"].lower()

    def test_pending_to_completed_direct_rejected(self, manager_api_client, booking):
        """pending → completed (sans confirmed) → 400."""
        resp = manager_api_client.post(f"/api/v1/bookings/{booking.id}/complete/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in resp.data

    def test_client_cannot_confirm_booking(self, client_api_client, booking):
        """Client ne peut PAS confirmer (réservé au gestionnaire) → 403."""
        resp = client_api_client.post(f"/api/v1/bookings/{booking.id}/confirm/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_client_cannot_complete_booking(self, client_api_client, booking):
        """Client ne peut PAS clôturer → 403."""
        booking.confirm()
        # Mettre les dates dans le passé pour pouvoir compléter
        booking.check_in = date.today() - timedelta(days=3)
        booking.check_out = date.today() - timedelta(days=1)
        booking.save(update_fields=["status", "check_in", "check_out"])
        resp = client_api_client.post(f"/api/v1/bookings/{booking.id}/complete/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_cannot_confirm_other_hotel_booking(self, manager_api_client, hotel_manager_user):
        """Gestionnaire d'un autre hôtel ne peut pas confirmer → 404 (pas dans son queryset)."""
        # Créer un autre hôtel avec un autre gestionnaire
        other_manager = UserFactory.create_hotel_manager()
        other_hotel = HotelFactory.create(manager=other_manager)
        other_room = RoomFactory.create(hotel=other_hotel)

        # Créer une résa pour l'autre hôtel
        client = UserFactory.create_client()
        check_in, check_out = _future_dates()
        booking = Booking.objects.create(
            user=client,
            hotel=other_hotel,
            room=other_room,
            check_in=check_in,
            check_out=check_out,
            adults=2,
            price_per_night=other_room.price_per_night,
            status=Booking.Status.PENDING,
        )

        # Gestionnaire original tente de confirmer → 404 (booking invisible dans son queryset)
        resp = manager_api_client.post(f"/api/v1/bookings/{booking.id}/confirm/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# 6. Règle délai d'annulation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCancellationDeadline:
    """Tests de la règle BOOKING_CANCELLATION_DEADLINE_DAYS (défaut: 2 jours)."""

    def test_cancel_within_deadline_allowed(self, client_api_client, room):
        """Annulation > 2 jours avant arrivée → autorisée."""
        check_in = date.today() + timedelta(days=5)  # 5 jours > deadline 2
        check_out = check_in + timedelta(days=2)
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        booking_id = resp.data["id"]

        resp_cancel = client_api_client.post(f"/api/v1/bookings/{booking_id}/cancel/")
        assert resp_cancel.status_code == status.HTTP_200_OK
        assert resp_cancel.data["status"] == Booking.Status.CANCELLED

    def test_cancel_after_deadline_rejected(self, client_api_client, room):
        """Annulation ≤ 2 jours avant arrivée → refusée (400)."""
        check_in = date.today() + timedelta(days=1)  # 1 jour < deadline 2
        check_out = check_in + timedelta(days=2)
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        booking_id = resp.data["id"]

        resp_cancel = client_api_client.post(f"/api/v1/bookings/{booking_id}/cancel/")
        assert resp_cancel.status_code == status.HTTP_400_BAD_REQUEST
        assert "délai" in resp_cancel.data["detail"].lower()

    def test_cancel_exactly_at_deadline_allowed(self, client_api_client, room):
        """Annulation exactement 2 jours avant → autorisée (check_in >= today+2 requis)."""
        # deadline = 2 jours → can_cancel si check_in >= today + 2
        # Si check_in = today + 2 → can_cancel = True
        # Si check_in = today + 1 → can_cancel = False
        check_in = _today() + timedelta(days=2)  # exactement au deadline
        check_out = check_in + timedelta(days=2)
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        booking_id = resp.data["id"]

        # Doit être autorisé (check_in >= today + 2)
        resp_cancel = client_api_client.post(f"/api/v1/bookings/{booking_id}/cancel/")
        assert resp_cancel.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# 7. Visibilité par rôle (ownership)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBookingOwnership:
    """Tests de visibilité : client voit ses résas, gestionnaire voit ses hôtels."""

    def test_client_lists_only_own_bookings(self, client_api_client, client_user, room):
        """GET /bookings/ ne retourne que les réservations du client connecté."""
        check_in, check_out = _future_dates(days_ahead=5, nights=2)
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        # Créer 2 réservations pour ce client
        resp1 = client_api_client.post("/api/v1/bookings/", payload, format="json")
        assert resp1.status_code == status.HTTP_201_CREATED

        check_in2 = check_out + timedelta(days=1)
        check_out2 = check_in2 + timedelta(days=2)
        payload2 = {
            "room": room.id,
            "check_in": check_in2.isoformat(),
            "check_out": check_out2.isoformat(),
            "adults": 1,
        }
        resp2 = client_api_client.post("/api/v1/bookings/", payload2, format="json")
        assert resp2.status_code == status.HTTP_201_CREATED

        # Lister
        resp_list = client_api_client.get("/api/v1/bookings/")
        assert resp_list.status_code == status.HTTP_200_OK
        results = resp_list.data.get("results", resp_list.data)  # support pagination
        assert len(results) == 2
        for b in results:
            assert b["user"] == client_user.email

    def test_client_cannot_view_other_client_booking(self, client_api_client, room, make_client):
        """Client A ne peut pas voir la réservation du Client B → 404."""
        # Client A crée une résa
        check_in, check_out = _future_dates()
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        booking_id = resp.data["id"]

        # Client B tente d'accéder
        other_client, other_user = make_client("client")
        other_client.force_authenticate(user=other_user)
        resp_get = other_client.get(f"/api/v1/bookings/{booking_id}/")
        assert resp_get.status_code == status.HTTP_404_NOT_FOUND

    def test_manager_lists_bookings_for_own_hotels(self, manager_api_client, hotel_manager_user, room):
        """Gestionnaire voit les réservations de SES hôtels."""
        # Créer une résa pour l'hôtel du gestionnaire
        check_in, check_out = _future_dates()
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        # Utiliser un client pour créer la résa
        from apps.accounts.models import User
        client = User.objects.create_user(
            email="client_for_manager_test@example.com",
            password="testpass123",
            role=User.Role.CLIENT,
        )
        from rest_framework.test import APIClient
        c = APIClient()
        c.force_authenticate(user=client)
        resp = c.post("/api/v1/bookings/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

        # Gestionnaire liste
        resp_list = manager_api_client.get("/api/v1/bookings/")
        assert resp_list.status_code == status.HTTP_200_OK
        results = resp_list.data.get("results", resp_list.data)
        assert len(results) >= 1
        for b in results:
            assert b["hotel"]["id"] == room.hotel_id

    def test_manager_cannot_view_other_hotel_bookings(self, manager_api_client, hotel_manager_user):
        """Gestionnaire ne voit PAS les réservations d'autres hôtels."""
        # Créer un autre hôtel avec un autre gestionnaire
        other_manager = UserFactory.create_hotel_manager()
        other_hotel = HotelFactory.create(manager=other_manager)
        other_room = RoomFactory.create(hotel=other_hotel)

        # Créer une résa pour l'autre hôtel
        client = UserFactory.create_client()
        from rest_framework.test import APIClient
        c = APIClient()
        c.force_authenticate(user=client)
        check_in, check_out = _future_dates()
        payload = {
            "room": other_room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = c.post("/api/v1/bookings/", payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        other_booking_id = resp.data["id"]

        # Gestionnaire original tente d'accéder → 404
        resp_get = manager_api_client.get(f"/api/v1/bookings/{other_booking_id}/")
        assert resp_get.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_sees_all_bookings(self, admin_api_client, room, make_client):
        """Admin (staff) voit toutes les réservations."""
        # Créer 2 clients, chacun une résa
        for i in range(2):
            c, u = make_client("client")
            check_in, check_out = _future_dates(days_ahead=5 + i * 3)
            payload = {
                "room": room.id,
                "check_in": check_in.isoformat(),
                "check_out": check_out.isoformat(),
                "adults": 2,
            }
            c.post("/api/v1/bookings/", payload, format="json")

        resp_list = admin_api_client.get("/api/v1/bookings/")
        assert resp_list.status_code == status.HTTP_200_OK
        results = resp_list.data.get("results", resp_list.data)
        assert len(results) >= 2


# ---------------------------------------------------------------------------
# 8. Filtrage par statut
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBookingStatusFilter:
    """Tests du filtre ?status= sur l'endpoint list."""

    def test_filter_status_pending(self, client_api_client, room):
        """?status=pending ne retourne que les pending."""
        check_in, check_out = _future_dates()
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        client_api_client.post("/api/v1/bookings/", payload, format="json")
        # Créer une confirmed
        check_in2 = check_out + timedelta(days=1)
        check_out2 = check_in2 + timedelta(days=2)
        payload2 = {
            "room": room.id,
            "check_in": check_in2.isoformat(),
            "check_out": check_out2.isoformat(),
            "adults": 1,
        }
        resp2 = client_api_client.post("/api/v1/bookings/", payload2, format="json")
        booking2_id = resp2.data["id"]
        # Confirmer la 2e
        from apps.bookings.models import Booking
        b2 = Booking.objects.get(id=booking2_id)
        b2.confirm()

        resp = client_api_client.get("/api/v1/bookings/?status=pending")
        assert resp.status_code == status.HTTP_200_OK
        results = resp.data.get("results", resp.data)
        for b in results:
            assert b["status"] == Booking.Status.PENDING

    def test_filter_status_confirmed(self, client_api_client, room):
        """?status=confirmed ne retourne que les confirmed."""
        check_in, check_out = _future_dates()
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        booking_id = resp.data["id"]
        b = Booking.objects.get(id=booking_id)
        b.confirm()

        resp = client_api_client.get("/api/v1/bookings/?status=confirmed")
        assert resp.status_code == status.HTTP_200_OK
        results = resp.data.get("results", resp.data)
        for b in results:
            assert b["status"] == Booking.Status.CONFIRMED

    def test_filter_status_cancelled(self, client_api_client, room):
        """?status=cancelled ne retourne que les cancelled."""
        check_in, check_out = _future_dates(days_ahead=10)
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        resp = client_api_client.post("/api/v1/bookings/", payload, format="json")
        booking_id = resp.data["id"]
        client_api_client.post(f"/api/v1/bookings/{booking_id}/cancel/")

        resp = client_api_client.get("/api/v1/bookings/?status=cancelled")
        assert resp.status_code == status.HTTP_200_OK
        results = resp.data.get("results", resp.data)
        for b in results:
            assert b["status"] == Booking.Status.CANCELLED

    def test_filter_invalid_status_returns_empty(self, client_api_client, room):
        """?status=invalid → liste vide (pas d'erreur 400)."""
        check_in, check_out = _future_dates()
        payload = {
            "room": room.id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
        }
        client_api_client.post("/api/v1/bookings/", payload, format="json")

        resp = client_api_client.get("/api/v1/bookings/?status=invalid")
        assert resp.status_code == status.HTTP_200_OK
        results = resp.data.get("results", resp.data)
        assert len(results) == 0


# ---------------------------------------------------------------------------
# Fixtures additionnelles pour les tests
# ---------------------------------------------------------------------------

@pytest.fixture
def hotel(hotel_manager_user):
    """Hôtel géré par hotel_manager_user."""
    return HotelFactory.create(manager=hotel_manager_user)


@pytest.fixture
def room(hotel):
    """Chambre dans l'hôtel du gestionnaire."""
    return RoomFactory.create(hotel=hotel, price_per_night=Decimal("120.00"))


@pytest.fixture
def booking(client_user, room):
    """Réservation PENDING pour client_user dans room."""
    check_in, check_out = _future_dates(days_ahead=10, nights=3)
    return Booking.objects.create(
        user=client_user,
        hotel=room.hotel,
        room=room,
        check_in=check_in,
        check_out=check_out,
        adults=2,
        children=0,
        price_per_night=room.price_per_night,
        status=Booking.Status.PENDING,
    )


# Import factories ici pour éviter les problèmes d'ordre
from apps.factories import HotelFactory, RoomFactory, UserFactory