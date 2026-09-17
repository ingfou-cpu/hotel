"""Tests pour l'API Notifications."""

import pytest
from rest_framework import status

from apps.notifications.models import Notification


# =============================================================================
# LISTING: USER SEES ONLY THEIR OWN NOTIFICATIONS
# =============================================================================

@pytest.mark.django_db
class TestNotificationListing:
    """Tests de listage des notifications."""

    def test_user_sees_only_own_notifications(self, client_api_client, make_client):
        """Un utilisateur ne voit que ses propres notifications."""
        # Notifications pour client_user
        Notification.objects.create(
            user=client_api_client.handler._force_user,
            type=Notification.Type.INFO,
            title="Bienvenue",
            message="Bienvenue sur la plateforme",
        )
        Notification.objects.create(
            user=client_api_client.handler._force_user,
            type=Notification.Type.BOOKING,
            title="Réservation confirmée",
            message="Votre réservation est confirmée",
        )
        # Autre utilisateur
        other_client, other_user = make_client("client")
        Notification.objects.create(
            user=other_user,
            type=Notification.Type.INFO,
            title="Pour l'autre",
            message="Message privé",
        )
        response = client_api_client.get("/api/v1/notifications/")
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert len(results) == 2
        for notif in results:
            assert notif["title"] in ("Bienvenue", "Réservation confirmée")

    def test_another_users_notifications_not_visible(self, client_api_client, make_client):
        """Notifications d'un autre utilisateur ne sont pas visibles."""
        other_client, other_user = make_client("client")
        Notification.objects.create(
            user=other_user,
            type=Notification.Type.INFO,
            title="Secret",
            message="Ne pas voir",
        )
        response = client_api_client.get("/api/v1/notifications/")
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert len(results) == 0


    def test_unauthenticated_user_gets_401(self, api_client):
        """Utilisateur non authentifié → 401."""
        response = api_client.get("/api/v1/notifications/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# READ/UNREAD STATUS
# =============================================================================

@pytest.mark.django_db
class TestNotificationReadUnread:
    """Tests du statut lu/non-lu."""

    def test_notification_defaults_to_unread(self, client_user):
        """Nouvelle notification → is_read=False par défaut."""
        notif = Notification.objects.create(
            user=client_user,
            type=Notification.Type.INFO,
            title="Test",
            message="Message",
        )
        assert notif.is_read is False

    def test_mark_single_notification_read(self, client_api_client, client_user):
        """Marquer une notification comme lue (POST /{pk}/read/)."""
        notif = Notification.objects.create(
            user=client_user,
            type=Notification.Type.INFO,
            title="À lire",
            message="Contenu",
            is_read=False,
        )
        response = client_api_client.post(f"/api/v1/notifications/{notif.id}/read/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_read"] is True
        notif.refresh_from_db()
        assert notif.is_read is True

    def test_mark_already_read_notification_idempotent(self, client_api_client, client_user):
        """Marquer une notification déjà lue → idempotent (200, is_read=True)."""
        notif = Notification.objects.create(
            user=client_user,
            type=Notification.Type.INFO,
            title="Déjà lu",
            message="Contenu",
            is_read=True,
        )
        response = client_api_client.post(f"/api/v1/notifications/{notif.id}/read/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_read"] is True

    def test_unread_filter_queryset_method(self, client_user):
        """QuerySet.unread() filtre correctement."""
        Notification.objects.create(
            user=client_user,
            type=Notification.Type.INFO,
            title="Non lu 1",
            message="",
            is_read=False,
        )
        Notification.objects.create(
            user=client_user,
            type=Notification.Type.INFO,
            title="Lu",
            message="",
            is_read=True,
        )
        Notification.objects.create(
            user=client_user,
            type=Notification.Type.INFO,
            title="Non lu 2",
            message="",
            is_read=False,
        )
        unread_qs = Notification.objects.filter(user=client_user).unread()
        assert unread_qs.count() == 2
        for n in unread_qs:
            assert n.is_read is False


# =============================================================================
# MARK_ALL_READ
# =============================================================================

@pytest.mark.django_db
class TestNotificationMarkAllRead:
    """Tests du marquage batch « tout lu »."""

    def test_mark_all_read_updates_all_unread(self, client_api_client, client_user):
        """POST /mark_all_read/ marque toutes les non-lues comme lues."""
        Notification.objects.create(
            user=client_user,
            type=Notification.Type.INFO,
            title="Non lu 1",
            message="",
            is_read=False,
        )
        Notification.objects.create(
            user=client_user,
            type=Notification.Type.BOOKING,
            title="Non lu 2",
            message="",
            is_read=False,
        )
        Notification.objects.create(
            user=client_user,
            type=Notification.Type.PAYMENT,
            title="Déjà lu",
            message="",
            is_read=True,
        )
        response = client_api_client.post("/api/v1/notifications/mark_all_read/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["updated"] == 2
        # Vérifier en base
        unread_count = Notification.objects.filter(user=client_user, is_read=False).count()
        assert unread_count == 0

    def test_mark_all_read_returns_zero_when_none_unread(self, client_api_client, client_user):
        """Si aucune non-lue → updated=0."""
        Notification.objects.create(
            user=client_user,
            type=Notification.Type.INFO,
            title="Déjà lu",
            message="",
            is_read=True,
        )
        response = client_api_client.post("/api/v1/notifications/mark_all_read/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["updated"] == 0

    def test_mark_all_read_only_affects_current_user(self, client_api_client, make_client, client_user):
        """mark_all_read ne touche qu'aux notifications de l'utilisateur courant."""
        other_client, other_user = make_client("client")
        Notification.objects.create(
            user=client_user,
            type=Notification.Type.INFO,
            title="Mon non lu",
            message="",
            is_read=False,
        )
        Notification.objects.create(
            user=other_user,
            type=Notification.Type.INFO,
            title="Son non lu",
            message="",
            is_read=False,
        )
        response = client_api_client.post("/api/v1/notifications/mark_all_read/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["updated"] == 1
        # L'autre utilisateur a toujours sa notification non-lue
        other_unread = Notification.objects.filter(user=other_user, is_read=False).count()
        assert other_unread == 1


# =============================================================================
# NOTIFICATION TYPES
# =============================================================================

@pytest.mark.django_db
class TestNotificationTypes:
    """Tests des types de notification valides."""

    @pytest.mark.parametrize("notif_type", [
        Notification.Type.INFO,
        Notification.Type.BOOKING,
        Notification.Type.PAYMENT,
        Notification.Type.CANCELLATION,
        Notification.Type.REMINDER,
    ])
    def test_create_notification_with_valid_type(self, client_user, notif_type):
        """Création avec chaque type valide (info/booking/payment/cancellation/reminder)."""
        notif = Notification.objects.create(
            user=client_user,
            type=notif_type,
            title=f"Test {notif_type}",
            message="Message",
        )
        assert notif.type == notif_type
        assert notif.get_type_display() != notif_type  # display value exists

    def test_notification_type_choices_are_correct(self):
        """Les choix de type correspondent aux valeurs attendues."""
        expected = {
            "info": "Information",
            "booking": "Réservation",
            "payment": "Paiement",
            "cancellation": "Annulation",
            "reminder": "Rappel",
        }
        assert dict(Notification.Type.choices) == expected

    def test_serializer_includes_type_display(self, client_api_client, client_user):
        """Le serializer inclut type_display (valeur lisible)."""
        notif = Notification.objects.create(
            user=client_user,
            type=Notification.Type.BOOKING,
            title="Réservation",
            message="Votre réservation est confirmée",
        )
        response = client_api_client.get(f"/api/v1/notifications/{notif.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["type"] == "booking"
        assert response.data["type_display"] == "Réservation"