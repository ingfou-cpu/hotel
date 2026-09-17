"""Configuration pytest partagée pour le backend HotelBooking."""

import random
import pytest
from django.conf import settings
from rest_framework.test import APIClient


# ---------------------------------------------------------------------------
# Celery : exécution synchrone pour les tests (pas de Redis requis)
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def celery_eager(settings):
    """Force Celery à exécuter les tâches immédiatement (mode eager)."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


# ---------------------------------------------------------------------------
# Clés Stripe factices pour éviter les crashes dans les vues de paiement
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def stripe_dummy_keys(settings):
    """Remplace les clés Stripe par des valeurs de test inoffensives."""
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    settings.STRIPE_WEBHOOK_SECRET = "whsec_dummy"
    settings.STRIPE_PUBLISHABLE_KEY = "pk_test_dummy"
    settings.STRIPE_CURRENCY = "eur"


# ---------------------------------------------------------------------------
# Helpers pour générer des valeurs uniques dans les tests
# ---------------------------------------------------------------------------
def _random_int() -> int:
    """Génère un entier aléatoire pour l'unicité des emails en tests."""
    return random.randint(10000, 999999)


# ---------------------------------------------------------------------------
# Clients API
# ---------------------------------------------------------------------------
@pytest.fixture
def api_client() -> APIClient:
    """Client DRF non authentifié."""
    return APIClient()


@pytest.fixture
def make_client(db, django_user_model):
    """Factory créant un APIClient authentifié pour un utilisateur fraîchement créé."""

    def _make_client(role: str = "client") -> APIClient:
        email = f"test_{role}_{_random_int()}@example.com"
        user = django_user_model.objects.create_user(
            email=email,
            password="testpass123",
            first_name="Test",
            last_name=role.capitalize(),
            role=role,
        )
        client = APIClient()
        client.force_authenticate(user=user)
        return client, user

    return _make_client


# Fixtures de commodité : utilisateurs
@pytest.fixture
def client_user(db, django_user_model):
    return django_user_model.objects.create_user(
        email="client@example.com",
        password="testpass123",
        first_name="Client",
        last_name="User",
        role="client",
    )


@pytest.fixture
def hotel_manager_user(db, django_user_model):
    return django_user_model.objects.create_user(
        email="manager@example.com",
        password="testpass123",
        first_name="Hotel",
        last_name="Manager",
        role="hotel_manager",
    )


@pytest.fixture
def admin_user(db, django_user_model):
    return django_user_model.objects.create_user(
        email="admin@example.com",
        password="testpass123",
        first_name="Admin",
        last_name="User",
        role="admin",
        is_staff=True,
        is_superuser=True,
    )


# Fixtures de commodité : clients authentifiés
@pytest.fixture
def client_api_client(api_client, client_user):
    api_client.force_authenticate(user=client_user)
    return api_client


@pytest.fixture
def manager_api_client(api_client, hotel_manager_user):
    api_client.force_authenticate(user=hotel_manager_user)
    return api_client


@pytest.fixture
def admin_api_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client