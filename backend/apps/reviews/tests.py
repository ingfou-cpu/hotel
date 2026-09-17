"""Tests pour l'API Avis (reviews)."""

import pytest
from decimal import Decimal
from django.db import IntegrityError
from rest_framework import status

from apps.hotels.models import Hotel
from apps.reviews.models import Review
from apps.bookings.models import Booking


# =============================================================================
# CREATE REVIEW
# =============================================================================

@pytest.mark.django_db
class TestReviewCreate:
    """Tests de création d'avis."""

    def test_authenticated_client_can_create_review(self, client_api_client, hotel_manager_user):
        """Client authentifié → 201."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        response = client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 5, "comment": "Excellent séjour"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["rating"] == 5
        assert response.data["comment"] == "Excellent séjour"
        assert response.data["user"] == client_api_client.handler._force_user.email

    def test_anonymous_user_cannot_create_review(self, api_client, hotel_manager_user):
        """Utilisateur anonyme → 401."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        response = api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 5, "comment": "Excellent séjour"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_rating_validation_rejects_zero(self, client_api_client, hotel_manager_user):
        """Note 0 → 400."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        response = client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 0, "comment": "Mauvais"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "rating" in response.data

    def test_rating_validation_rejects_six(self, client_api_client, hotel_manager_user):
        """Note 6 → 400."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        response = client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 6, "comment": "Trop bien"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "rating" in response.data

    def test_rating_validation_accepts_one(self, client_api_client, hotel_manager_user):
        """Note 1 → 201."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        response = client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 1, "comment": "Médiocre"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["rating"] == 1

    def test_rating_validation_accepts_five(self, client_api_client, hotel_manager_user):
        """Note 5 → 201."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        response = client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 5, "comment": "Parfait"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["rating"] == 5


# =============================================================================
# UNIQUE CONSTRAINT: ONE REVIEW PER USER/HOTEL
# =============================================================================

@pytest.mark.django_db
class TestReviewUniqueConstraint:
    """Tests de contrainte d'unicité (un avis par user/hotel)."""

    def test_second_review_same_user_hotel_returns_400(self, client_api_client, hotel_manager_user):
        """Deuxième avis même user+hôtel → 400."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        # Premier avis
        client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 4, "comment": "Premier avis"},
            format="json",
        )
        # Deuxième avis
        response = client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 5, "comment": "Deuxième avis"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "hotel" in response.data

    def test_unique_constraint_at_database_level(self, client_user, hotel_manager_user):
        """Contrainte DB unique_review_per_user_hotel bloque la duplication."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        Review.objects.create(user=client_user, hotel=hotel, rating=3, comment="Avis 1")
        with pytest.raises(IntegrityError):
            Review.objects.create(user=client_user, hotel=hotel, rating=4, comment="Avis 2")


# =============================================================================
# DENORMALIZATION SIGNAL: HOTEL AVERAGE_RATING & REVIEWS_COUNT
# =============================================================================

@pytest.mark.django_db
class TestHotelDenormalizationSignal:
    """Tests du signal de dénormalisation sur Hotel."""

    def test_hotel_updates_after_single_review(self, client_api_client, hotel_manager_user):
        """Après un avis, average_rating et reviews_count sont mis à jour."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
            average_rating=Decimal("0.00"),
            reviews_count=0,
        )
        client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 4, "comment": "Bien"},
            format="json",
        )
        hotel.refresh_from_db()
        assert hotel.reviews_count == 1
        assert float(hotel.average_rating) == 4.00

    def test_hotel_updates_after_multiple_reviews_correct_average(
        self, client_api_client, client_user, make_client, hotel_manager_user
    ):
        """Plusieurs avis → moyenne correcte."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
            average_rating=Decimal("0.00"),
            reviews_count=0,
        )
        # Client 1 : note 2
        client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 2, "comment": "Moyen"},
            format="json",
        )
        # Client 2 : note 4
        client2_client, client2_user = make_client("client")
        client2_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 4, "comment": "Bien"},
            format="json",
        )
        # Client 3 : note 5
        client3_client, client3_user = make_client("client")
        client3_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 5, "comment": "Excellent"},
            format="json",
        )
        hotel.refresh_from_db()
        assert hotel.reviews_count == 3
        # (2 + 4 + 5) / 3 = 3.666... → arrondi à 2 décimales
        assert float(hotel.average_rating) == 3.67

    def test_hotel_updates_after_review_deletion(self, client_api_client, hotel_manager_user):
        """Suppression d'avis met à jour les compteurs."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
            average_rating=Decimal("0.00"),
            reviews_count=0,
        )
        create_resp = client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 5, "comment": "Top"},
            format="json",
        )
        review_id = create_resp.data["id"]
        hotel.refresh_from_db()
        assert hotel.reviews_count == 1
        assert float(hotel.average_rating) == 5.00

        # Suppression
        delete_resp = client_api_client.delete(f"/api/v1/reviews/{review_id}/")
        assert delete_resp.status_code == status.HTTP_204_NO_CONTENT
        hotel.refresh_from_db()
        assert hotel.reviews_count == 0
        assert float(hotel.average_rating) == 0.00


# =============================================================================
# OWNER-ONLY EDIT/DELETE (IsOwnerOrReadOnly)
# =============================================================================

@pytest.mark.django_db
class TestReviewOwnerPermissions:
    """Tests de permissions propriétaire seul (IsOwnerOrReadOnly)."""

    def test_author_can_update_own_review(self, client_api_client, hotel_manager_user):
        """Auteur peut modifier son avis (PATCH)."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        create_resp = client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 3, "comment": "OK"},
            format="json",
        )
        review_id = create_resp.data["id"]
        patch_resp = client_api_client.patch(
            f"/api/v1/reviews/{review_id}/",
            {"rating": 5, "comment": "En fait c'était génial"},
            format="json",
        )
        assert patch_resp.status_code == status.HTTP_200_OK
        assert patch_resp.data["rating"] == 5
        assert patch_resp.data["comment"] == "En fait c'était génial"

    def test_author_can_delete_own_review(self, client_api_client, hotel_manager_user):
        """Auteur peut supprimer son avis (DELETE)."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        create_resp = client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 3, "comment": "OK"},
            format="json",
        )
        review_id = create_resp.data["id"]
        delete_resp = client_api_client.delete(f"/api/v1/reviews/{review_id}/")
        assert delete_resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Review.objects.filter(id=review_id).exists()

    def test_another_client_cannot_update_review(self, client_api_client, make_client, hotel_manager_user):
        """Autre client → 403/404 sur modification."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        create_resp = client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 3, "comment": "OK"},
            format="json",
        )
        review_id = create_resp.data["id"]
        other_client, _ = make_client("client")
        patch_resp = other_client.patch(
            f"/api/v1/reviews/{review_id}/",
            {"rating": 1, "comment": "Hacked"},
            format="json",
        )
        # IsOwnerOrReadOnly renvoie 403 (permission denied)
        assert patch_resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)

    def test_another_client_cannot_delete_review(self, client_api_client, make_client, hotel_manager_user):
        """Autre client → 403/404 sur suppression."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        create_resp = client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 3, "comment": "OK"},
            format="json",
        )
        review_id = create_resp.data["id"]
        other_client, _ = make_client("client")
        delete_resp = other_client.delete(f"/api/v1/reviews/{review_id}/")
        assert delete_resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)

    def test_owner_cannot_edit_another_users_review(self, make_client, hotel_manager_user):
        """Un client ne peut pas éditer l'avis d'un autre client."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        client1, user1 = make_client("client")
        create_resp = client1.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 4, "comment": "Avis client 1"},
            format="json",
        )
        review_id = create_resp.data["id"]
        client2, _ = make_client("client")
        patch_resp = client2.patch(
            f"/api/v1/reviews/{review_id}/",
            {"rating": 1, "comment": "Tentative"},
            format="json",
        )
        assert patch_resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)


# =============================================================================
# HOTEL REVIEW LIST ENDPOINT
# =============================================================================

@pytest.mark.django_db
class TestHotelReviewList:
    """Tests de listage des avis (filtre ?hotel=)."""

    def test_list_reviews_filtered_by_hotel(self, client_api_client, make_client, hotel_manager_user):
        """GET /api/reviews/?hotel=<id> liste les avis de cet hôtel."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        other_hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Other Hotel",
            description="Description",
            address="456 Rue Autre",
            city="Lyon",
            country="France",
            latitude=Decimal("45.7640"),
            longitude=Decimal("4.8357"),
            stars=4,
        )
        # Avis sur hotel
        client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 5, "comment": "Super"},
            format="json",
        )
        # Avis sur other_hotel par autre client
        other_client, _ = make_client("client")
        other_client.post(
            "/api/v1/reviews/",
            {"hotel": other_hotel.id, "rating": 3, "comment": "Moyen"},
            format="json",
        )
        # Filtrer par hotel
        response = client_api_client.get(f"/api/v1/reviews/?hotel={hotel.id}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["hotel_details"]["id"] == hotel.id

    def test_list_reviews_public_access(self, api_client, client_user, hotel_manager_user):
        """Listage public (sans auth) fonctionne."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        Review.objects.create(user=client_user, hotel=hotel, rating=4, comment="Public visible")
        response = api_client.get(f"/api/v1/reviews/?hotel={hotel.id}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_reviews_ordered_by_created_at_desc(self, client_api_client, make_client, hotel_manager_user):
        """Avis triés par created_at décroissant."""
        hotel = Hotel.objects.create(
            manager=hotel_manager_user,
            name="Test Hotel",
            description="Description",
            address="123 Rue Test",
            city="Paris",
            country="France",
            latitude=Decimal("48.8566"),
            longitude=Decimal("2.3522"),
            stars=3,
        )
        client_api_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 3, "comment": "Premier"},
            format="json",
        )
        other_client, _ = make_client("client")
        other_client.post(
            "/api/v1/reviews/",
            {"hotel": hotel.id, "rating": 5, "comment": "Deuxième (plus récent)"},
            format="json",
        )
        response = client_api_client.get(f"/api/v1/reviews/?hotel={hotel.id}")
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert len(results) == 2
        # Le plus récent en premier
        assert results[0]["comment"] == "Deuxième (plus récent)"
        assert results[1]["comment"] == "Premier"