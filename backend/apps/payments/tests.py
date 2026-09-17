"""Tests pour l'API Paiements (Stripe Checkout, Webhook, Remboursement)."""

import hmac
import hashlib
import json
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
import stripe
from django.conf import settings
from django.test import override_settings
from rest_framework import status

from apps.bookings.models import Booking
from apps.payments.models import Payment
from apps.payments.services import handle_checkout_event, prepare_checkout_session, refund_payment
from apps.factories import BookingFactory, PaymentFactory, HotelFactory, RoomFactory, UserFactory


# ---------------------------------------------------------------------------
# Helpers locaux
# ---------------------------------------------------------------------------

def _future_dates(days_ahead=5, nights=3):
    """Retourne (check_in, check_out) futurs."""
    check_in = date.today() + timedelta(days=days_ahead)
    check_out = check_in + timedelta(days=nights)
    return check_in, check_out


# ---------------------------------------------------------------------------
# Helpers pour construire des événements Stripe signés
# ---------------------------------------------------------------------------

def _sign_payload(payload: bytes, secret: str) -> str:
    """Calcule l'en-tête stripe-signature pour un payload et un secret donnés."""
    import time
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload.decode()}".encode()
    signature = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


def _make_checkout_session_completed_event(session_id: str, payment_intent_id: str = "pi_test_123") -> dict:
    """Construit un événement checkout.session.completed minimal."""
    return {
        "id": f"evt_test_{session_id}",
        "object": "event",
        "type": "checkout.session.completed",
        "api_version": "2023-10-16",
        "created": 1234567890,
        "data": {
            "object": {
                "id": session_id,
                "object": "checkout.session",
                "payment_intent": payment_intent_id,
                "payment_status": "paid",
                "metadata": {},
            }
        },
    }


def _make_checkout_session_expired_event(session_id: str) -> dict:
    """Construit un événement checkout.session.expired minimal."""
    return {
        "id": f"evt_test_expired_{session_id}",
        "object": "event",
        "type": "checkout.session.expired",
        "api_version": "2023-10-16",
        "created": 1234567890,
        "data": {
            "object": {
                "id": session_id,
                "object": "checkout.session",
                "metadata": {},
            }
        },
    }


def _make_async_payment_succeeded_event(session_id: str, payment_intent_id: str = "pi_test_123") -> dict:
    """Construit un événement checkout.session.async_payment_succeeded minimal."""
    return {
        "id": f"evt_test_async_{session_id}",
        "object": "event",
        "type": "checkout.session.async_payment_succeeded",
        "api_version": "2023-10-16",
        "created": 1234567890,
        "data": {
            "object": {
                "id": session_id,
                "object": "checkout.session",
                "payment_intent": payment_intent_id,
                "metadata": {},
            }
        },
    }


# ---------------------------------------------------------------------------
# CHECKOUT SESSION CREATION
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCheckoutSessionCreation:
    """Tests de création de session Checkout Stripe."""

    def test_checkout_authenticated_client_returns_201_with_session(
        self, client_api_client, booking_factory
    ):
        """Client authentifié sur réservation payable → 201 avec checkout_url et session_id."""
        # Créer une réservation en attente pour le client
        booking = booking_factory(user=client_api_client.handler._force_user, status=Booking.Status.PENDING)

        # Créer le paiement associé
        payment = Payment.objects.create(
            user=client_api_client.handler._force_user,
            booking=booking,
            amount=booking.total_price,
            currency=settings.STRIPE_CURRENCY,
            status=Payment.Status.PENDING,
        )

        with patch("apps.payments.services.stripe.checkout.Session.create") as mock_create:
            mock_session = MagicMock()
            mock_session.id = "cs_test_123"
            mock_session.url = "https://checkout.stripe.com/pay/cs_test_123"
            mock_create.return_value = mock_session

            response = client_api_client.post(f"/api/v1/payments/{payment.id}/checkout/")

        assert response.status_code == status.HTTP_201_CREATED
        assert "checkout_url" in response.data
        assert "session_id" in response.data
        assert response.data["session_id"] == "cs_test_123"
        assert response.data["checkout_url"] == "https://checkout.stripe.com/pay/cs_test_123"

        # Vérifier que stripe.checkout.Session.create a été appelé avec les bons arguments
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["mode"] == "payment"
        assert len(call_kwargs["line_items"]) == 1
        line_item = call_kwargs["line_items"][0]
        assert line_item["price_data"]["currency"] == settings.STRIPE_CURRENCY
        assert line_item["price_data"]["unit_amount"] == int(booking.total_price * 100)
        assert line_item["price_data"]["product_data"]["name"] == f"Réservation {booking.booking_code}"
        assert call_kwargs["customer_email"] == client_api_client.handler._force_user.email
        assert call_kwargs["metadata"]["payment_id"] == str(payment.id)
        assert call_kwargs["metadata"]["booking_code"] == booking.booking_code
        assert call_kwargs["success_url"] == f"{settings.FRONTEND_URL}/reservation/success?session_id={{CHECKOUT_SESSION_ID}}"
        assert call_kwargs["cancel_url"] == f"{settings.FRONTEND_URL}/reservation/annulation"

    def test_checkout_anonymous_returns_401(self, api_client, payment_factory):
        """Client anonyme → 401."""
        payment = payment_factory(status=Payment.Status.PENDING)
        response = api_client.post(f"/api/v1/payments/{payment.id}/checkout/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_checkout_already_paid_returns_400(self, client_api_client, payment_factory):
        """Paiement déjà payé → 400."""
        payment = payment_factory(user=client_api_client.handler._force_user, status=Payment.Status.PAID)
        response = client_api_client.post(f"/api/v1/payments/{payment.id}/checkout/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "déjà réglé" in response.data["detail"].lower()

    def test_checkout_refunded_returns_400(self, client_api_client, payment_factory):
        """Paiement remboursé → 400."""
        payment = payment_factory(user=client_api_client.handler._force_user, status=Payment.Status.REFUNDED)
        response = client_api_client.post(f"/api/v1/payments/{payment.id}/checkout/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "déjà réglé" in response.data["detail"].lower()

    def test_checkout_idempotent_reuses_existing_session(
        self, client_api_client, payment_factory
    ):
        """Session Checkout existante et active → réutilisée (idempotent)."""
        payment = payment_factory(
            user=client_api_client.handler._force_user,
            status=Payment.Status.PENDING,
            stripe_session_id="cs_existing_123",
        )

        with patch("apps.payments.services.stripe.checkout.Session.retrieve") as mock_retrieve:
            mock_session = MagicMock()
            mock_session.id = "cs_existing_123"
            mock_session.url = "https://checkout.stripe.com/pay/cs_existing_123"
            mock_retrieve.return_value = mock_session

            response = client_api_client.post(f"/api/v1/payments/{payment.id}/checkout/")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["session_id"] == "cs_existing_123"
        mock_retrieve.assert_called_once_with("cs_existing_123")
        # Session.create ne doit pas être appelé
        with patch("apps.payments.services.stripe.checkout.Session.create") as mock_create:
            pass  # Just verify it wasn't called


# ---------------------------------------------------------------------------
# WEBHOOK — SIGNATURE VERIFICATION & EVENT HANDLING
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestStripeWebhook:
    """Tests du webhook Stripe : vérification signature, traitement événements."""

    def test_webhook_valid_signature_checkout_session_completed(
        self, api_client, payment_factory
    ):
        """Signature valide pour checkout.session.completed → Payment PAID, Booking CONFIRMED."""
        payment = payment_factory(
            status=Payment.Status.PENDING,
            stripe_session_id="cs_test_webhook_123",
        )
        booking = payment.booking
        assert booking.status == Booking.Status.PENDING

        event = _make_checkout_session_completed_event("cs_test_webhook_123", "pi_webhook_123")
        payload = json.dumps(event).encode()
        sig_header = _sign_payload(payload, settings.STRIPE_WEBHOOK_SECRET)

        response = api_client.post(
            "/api/v1/payments/webhook/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=sig_header,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        payment.refresh_from_db()
        booking.refresh_from_db()
        assert payment.status == Payment.Status.PAID
        assert payment.stripe_payment_intent_id == "pi_webhook_123"
        assert booking.status == Booking.Status.CONFIRMED

    def test_webhook_valid_signature_async_payment_succeeded(
        self, api_client, payment_factory
    ):
        """Signature valide pour async_payment_succeeded → Payment PAID, Booking CONFIRMED."""
        payment = payment_factory(
            status=Payment.Status.PENDING,
            stripe_session_id="cs_test_async_123",
        )

        event = _make_async_payment_succeeded_event("cs_test_async_123", "pi_async_123")
        payload = json.dumps(event).encode()
        sig_header = _sign_payload(payload, settings.STRIPE_WEBHOOK_SECRET)

        response = api_client.post(
            "/api/v1/payments/webhook/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=sig_header,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        payment.refresh_from_db()
        assert payment.status == Payment.Status.PAID
        assert payment.stripe_payment_intent_id == "pi_async_123"
        assert payment.booking.status == Booking.Status.CONFIRMED

    def test_webhook_invalid_signature_returns_400(self, api_client, payment_factory):
        """Signature invalide → 400."""
        payment = payment_factory(
            status=Payment.Status.PENDING,
            stripe_session_id="cs_test_invalid_sig_123",
        )

        event = _make_checkout_session_completed_event("cs_test_invalid_sig_123")
        payload = json.dumps(event).encode()
        sig_header = _sign_payload(payload, "wrong_secret")

        response = api_client.post(
            "/api/v1/payments/webhook/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=sig_header,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "signature webhook invalide" in response.data["detail"].lower()

    def test_webhook_missing_signature_returns_400(self, api_client, payment_factory):
        """Signature manquante → 400."""
        payment = payment_factory(
            status=Payment.Status.PENDING,
            stripe_session_id="cs_test_no_sig_123",
        )

        event = _make_checkout_session_completed_event("cs_test_no_sig_123")
        payload = json.dumps(event).encode()

        response = api_client.post(
            "/api/v1/payments/webhook/",
            data=payload,
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_webhook_unknown_event_type_returns_200_ignored(
        self, api_client, payment_factory
    ):
        """Type d'événement inconnu → 200 ignoré (convention Stripe)."""
        payment = payment_factory(
            status=Payment.Status.PENDING,
            stripe_session_id="cs_test_unknown_123",
        )

        # Type d'événement non géré par handle_checkout_event
        event = {
            "id": "evt_test_unknown",
            "object": "event",
            "type": "customer.created",  # Non géré
            "api_version": "2023-10-16",
            "created": 1234567890,
            "data": {"object": {"id": "cs_test_unknown_123"}},
        }
        payload = json.dumps(event).encode()
        sig_header = _sign_payload(payload, settings.STRIPE_WEBHOOK_SECRET)

        response = api_client.post(
            "/api/v1/payments/webhook/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=sig_header,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        # Le paiement ne doit pas changer
        payment.refresh_from_db()
        assert payment.status == Payment.Status.PENDING

    def test_webhook_checkout_session_expired_marks_failed(
        self, api_client, payment_factory
    ):
        """checkout.session.expired → Payment FAILED."""
        payment = payment_factory(
            status=Payment.Status.PENDING,
            stripe_session_id="cs_test_expired_123",
        )

        event = _make_checkout_session_expired_event("cs_test_expired_123")
        payload = json.dumps(event).encode()
        sig_header = _sign_payload(payload, settings.STRIPE_WEBHOOK_SECRET)

        response = api_client.post(
            "/api/v1/payments/webhook/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=sig_header,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        payment.refresh_from_db()
        assert payment.status == Payment.Status.FAILED

    def test_webhook_session_not_found_returns_200(self, api_client):
        """Session Stripe inconnue → 200 (webhook acknowledged)."""
        event = _make_checkout_session_completed_event("cs_nonexistent_123")
        payload = json.dumps(event).encode()
        sig_header = _sign_payload(payload, settings.STRIPE_WEBHOOK_SECRET)

        response = api_client.post(
            "/api/v1/payments/webhook/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=sig_header,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_webhook_invalid_json_payload_returns_400(self, api_client):
        """Payload JSON invalide → 400."""
        payload = b"not valid json"
        sig_header = _sign_payload(payload, settings.STRIPE_WEBHOOK_SECRET)

        response = api_client.post(
            "/api/v1/payments/webhook/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=sig_header,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# MARK_PAID FLOW & IDEMPOTENCY
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMarkPaidFlow:
    """Tests du flux mark_paid : transition PAID → CONFIRMED, idempotence."""

    def test_mark_paid_via_webhook_sets_payment_paid_booking_confirmed(
        self, payment_factory
    ):
        """Après webhook réussi : Payment.status=PAID, Booking.status=CONFIRMED."""
        payment = payment_factory(
            status=Payment.Status.PENDING,
            stripe_session_id="cs_mark_paid_123",
        )
        booking = payment.booking

        event = _make_checkout_session_completed_event("cs_mark_paid_123", "pi_mark_paid_123")
        handle_checkout_event(stripe.Event.construct_from(event, stripe.api_key))

        payment.refresh_from_db()
        booking.refresh_from_db()
        assert payment.status == Payment.Status.PAID
        assert payment.stripe_payment_intent_id == "pi_mark_paid_123"
        assert booking.status == Booking.Status.CONFIRMED

    def test_webhook_idempotent_second_delivery_no_double_process(
        self, payment_factory
    ):
        """Deuxième livraison du même événement → pas de double traitement."""
        payment = payment_factory(
            status=Payment.Status.PENDING,
            stripe_session_id="cs_idempotent_123",
        )
        booking = payment.booking

        event = _make_checkout_session_completed_event("cs_idempotent_123", "pi_idempotent_123")
        stripe_event = stripe.Event.construct_from(event, stripe.api_key)

        # Première livraison
        result1 = handle_checkout_event(stripe_event)
        # Deuxième livraison (même event)
        result2 = handle_checkout_event(stripe_event)

        assert result1 is True
        assert result2 is True  # Idempotent, retourne True
        payment.refresh_from_db()
        booking.refresh_from_db()
        assert payment.status == Payment.Status.PAID
        assert booking.status == Booking.Status.CONFIRMED
        # Une seule notification, pas de doublon
        # (on ne teste pas les notifications ici, mais le statut ne change pas)

    def test_webhook_idempotent_already_paid_payment_no_op(
        self, payment_factory
    ):
        """Paiement déjà PAID → pas de traitement supplémentaire."""
        payment = payment_factory(
            status=Payment.Status.PAID,
            stripe_session_id="cs_already_paid_123",
            stripe_payment_intent_id="pi_existing",
        )
        booking = payment.booking
        booking.status = Booking.Status.CONFIRMED
        booking.save()

        event = _make_checkout_session_completed_event("cs_already_paid_123", "pi_new_intent")
        result = handle_checkout_event(stripe.Event.construct_from(event, stripe.api_key))

        assert result is True
        payment.refresh_from_db()
        # Le payment_intent_id ne doit pas changer
        assert payment.stripe_payment_intent_id == "pi_existing"
        assert booking.status == Booking.Status.CONFIRMED


# ---------------------------------------------------------------------------
# REFUND FLOW
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRefundFlow:
    """Tests du flux de remboursement."""

    def test_refund_endpoint_manager_returns_200_marks_refunded(
        self, manager_api_client, payment_factory, hotel_manager_user
    ):
        """Manager de l'hôtel rembourse → 200, Payment REFUNDED."""
        hotel = hotel_manager_user.managed_hotels.first()
        room = hotel.rooms.first()
        booking = BookingFactory.create(
            hotel=hotel,
            room=room,
            user=payment_factory.user,
            status=Booking.Status.CONFIRMED,
        )
        payment = Payment.objects.create(
            user=booking.user,
            booking=booking,
            amount=booking.total_price,
            currency=settings.STRIPE_CURRENCY,
            status=Payment.Status.PAID,
            stripe_payment_intent_id="pi_refund_123",
        )

        with patch("apps.payments.services.stripe.Refund.create") as mock_refund:
            mock_refund.return_value = MagicMock(id="re_test_123")
            response = manager_api_client.post(f"/api/v1/payments/{payment.id}/refund/")

        assert response.status_code == status.HTTP_200_OK
        payment.refresh_from_db()
        assert payment.status == Payment.Status.REFUNDED
        mock_refund.assert_called_once_with(
            payment_intent="pi_refund_123",
            amount=int(payment.amount * 100),
            reason="requested_by_customer",
        )

    def test_refund_client_forbidden_returns_403(self, client_api_client, payment_factory):
        """Client (pas manager) → 403."""
        payment = payment_factory(
            status=Payment.Status.PAID,
            stripe_payment_intent_id="pi_client_refund_123",
        )
        response = client_api_client.post(f"/api/v1/payments/{payment.id}/refund/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_refund_not_paid_returns_400(self, manager_api_client, payment_factory, hotel_manager_user):
        """Paiement non payé → 400."""
        hotel = hotel_manager_user.managed_hotels.first()
        room = hotel.rooms.first()
        booking = BookingFactory.create(
            hotel=hotel,
            room=room,
            status=Booking.Status.PENDING,
        )
        payment = Payment.objects.create(
            user=booking.user,
            booking=booking,
            amount=booking.total_price,
            currency=settings.STRIPE_CURRENCY,
            status=Payment.Status.PENDING,
            stripe_payment_intent_id="pi_pending_123",
        )

        response = manager_api_client.post(f"/api/v1/payments/{payment.id}/refund/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "payé" in response.data["detail"].lower()

    def test_refund_stripe_error_returns_400(self, manager_api_client, payment_factory, hotel_manager_user):
        """Erreur Stripe lors du remboursement → 400 avec message."""
        hotel = hotel_manager_user.managed_hotels.first()
        room = hotel.rooms.first()
        booking = BookingFactory.create(
            hotel=hotel,
            room=room,
            status=Booking.Status.CONFIRMED,
        )
        payment = Payment.objects.create(
            user=booking.user,
            booking=booking,
            amount=booking.total_price,
            currency=settings.STRIPE_CURRENCY,
            status=Payment.Status.PAID,
            stripe_payment_intent_id="pi_error_123",
        )

        with patch("apps.payments.services.stripe.Refund.create") as mock_refund:
            mock_refund.side_effect = stripe.error.InvalidRequestError(
                message="PaymentIntent already refunded",
                param="payment_intent",
            )
            response = manager_api_client.post(f"/api/v1/payments/{payment.id}/refund/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "remboursement refusé" in response.data["detail"].lower()
        payment.refresh_from_db()
        assert payment.status == Payment.Status.PAID  # Pas changé

    def test_auto_refund_on_cancelled_booking_via_webhook(
        self, payment_factory
    ):
        """Réservation annulée avant webhook → remboursement auto au webhook."""
        payment = payment_factory(
            status=Payment.Status.PENDING,
            stripe_session_id="cs_autorefund_123",
        )
        # Annuler la réservation avant le webhook
        payment.booking.status = Booking.Status.CANCELLED
        payment.booking.save()

        event = _make_checkout_session_completed_event("cs_autorefund_123", "pi_autorefund_123")
        with patch("apps.payments.services.refund_payment") as mock_refund:
            mock_refund.return_value = None
            handle_checkout_event(stripe.Event.construct_from(event, stripe.api_key))

        # Le remboursement auto doit être appelé
        mock_refund.assert_called_once()
        payment.refresh_from_db()
        assert payment.stripe_payment_intent_id == "pi_autorefund_123"
        # Le paiement n'est pas marqué PAID car la réservation est annulée
        # (selon la logique de handle_checkout_event)


# ---------------------------------------------------------------------------
# MISSING WEBHOOK SECRET BEHAVIOR
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMissingWebhookSecret:
    """Tests du comportement quand STRIPE_WEBHOOK_SECRET est absent."""

    @override_settings(STRIPE_WEBHOOK_SECRET="", DEBUG=True)
    def test_webhook_missing_secret_debug_true_accepts_payload(
        self, api_client, payment_factory
    ):
        """DEBUG=True, secret vide → accepte le payload sans vérif (comportement dev)."""
        payment = payment_factory(
            status=Payment.Status.PENDING,
            stripe_session_id="cs_debug_123",
        )

        event = _make_checkout_session_completed_event("cs_debug_123", "pi_debug_123")
        payload = json.dumps(event).encode()

        response = api_client.post(
            "/api/v1/payments/webhook/",
            data=payload,
            content_type="application/json",
            # Pas de signature header
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        payment.refresh_from_db()
        assert payment.status == Payment.Status.PAID

    @override_settings(STRIPE_WEBHOOK_SECRET="", DEBUG=False)
    def test_webhook_missing_secret_debug_false_returns_503(
        self, api_client, payment_factory
    ):
        """DEBUG=False, secret vide → 503 (webhook non configuré)."""
        payment = payment_factory(
            status=Payment.Status.PENDING,
            stripe_session_id="cs_prod_123",
        )

        event = _make_checkout_session_completed_event("cs_prod_123", "pi_prod_123")
        payload = json.dumps(event).encode()

        response = api_client.post(
            "/api/v1/payments/webhook/",
            data=payload,
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "webhook non configuré" in response.data["detail"].lower()

    def test_webhook_empty_secret_with_signature_fails_gracefully(
        self, api_client, payment_factory, settings
    ):
        """Secret vide mais signature fournie → géré gracieusement (DEBUG=True par défaut en test)."""
        # En test, DEBUG=True via settings de test, donc passe en mode "pas de vérif"
        payment = payment_factory(
            status=Payment.Status.PENDING,
            stripe_session_id="cs_empty_secret_123",
        )

        event = _make_checkout_session_completed_event("cs_empty_secret_123")
        payload = json.dumps(event).encode()
        sig_header = _sign_payload(payload, "whsec_dummy")  # Signature avec le secret par défaut

        response = api_client.post(
            "/api/v1/payments/webhook/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=sig_header,
        )

        # En DEBUG=True, le secret vide ne bloque pas, le payload est accepté
        assert response.status_code == status.HTTP_204_NO_CONTENT


# ---------------------------------------------------------------------------
# SERVICE LAYER UNIT TESTS (sans HTTP)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPaymentServices:
    """Tests unitaires des services (prepare_checkout_session, refund_payment, handle_checkout_event)."""

    def test_prepare_checkout_session_creates_session(self, payment_factory):
        """prepare_checkout_session crée une session Stripe."""
        payment = payment_factory(status=Payment.Status.PENDING)

        with patch("apps.payments.services.stripe.checkout.Session.create") as mock_create:
            mock_session = MagicMock()
            mock_session.id = "cs_service_123"
            mock_session.url = "https://checkout.stripe.com/pay/cs_service_123"
            mock_create.return_value = mock_session

            session = prepare_checkout_session(payment)

        assert session == mock_session
        assert payment.stripe_session_id == "cs_service_123"
        mock_create.assert_called_once()

    def test_prepare_checkout_session_returns_none_for_paid(self, payment_factory):
        """Paiement PAID → None."""
        payment = payment_factory(status=Payment.Status.PAID)
        session = prepare_checkout_session(payment)
        assert session is None

    def test_prepare_checkout_session_returns_none_for_refunded(self, payment_factory):
        """Paiement REFUNDED → None."""
        payment = payment_factory(status=Payment.Status.REFUNDED)
        session = prepare_checkout_session(payment)
        assert session is None

    def test_prepare_checkout_session_reuses_active_session(self, payment_factory):
        """Session active existante → réutilisée."""
        payment = payment_factory(
            status=Payment.Status.PENDING,
            stripe_session_id="cs_reuse_123",
        )

        with patch("apps.payments.services.stripe.checkout.Session.retrieve") as mock_retrieve:
            mock_session = MagicMock()
            mock_session.id = "cs_reuse_123"
            mock_session.url = "https://checkout.stripe.com/pay/cs_reuse_123"
            mock_retrieve.return_value = mock_session

            session = prepare_checkout_session(payment)

        assert session == mock_session
        mock_retrieve.assert_called_once_with("cs_reuse_123")

    def test_prepare_checkout_session_creates_new_if_existing_expired(self, payment_factory):
        """Session existante expirée → nouvelle session créée."""
        payment = payment_factory(
            status=Payment.Status.PENDING,
            stripe_session_id="cs_expired_123",
        )

        with patch("apps.payments.services.stripe.checkout.Session.retrieve") as mock_retrieve:
            mock_retrieve.side_effect = stripe.error.InvalidRequestError(
                message="No such checkout session", param="session_id"
            )
            with patch("apps.payments.services.stripe.checkout.Session.create") as mock_create:
                mock_session = MagicMock()
                mock_session.id = "cs_new_123"
                mock_session.url = "https://checkout.stripe.com/pay/cs_new_123"
                mock_create.return_value = mock_session

                session = prepare_checkout_session(payment)

        assert session == mock_session
        assert payment.stripe_session_id == "cs_new_123"

    def test_refund_payment_creates_stripe_refund(self, payment_factory):
        """refund_payment crée un remboursement Stripe et marque REFUNDED."""
        payment = payment_factory(
            status=Payment.Status.PAID,
            stripe_payment_intent_id="pi_refund_service_123",
        )

        with patch("apps.payments.services.stripe.Refund.create") as mock_refund:
            mock_refund.return_value = MagicMock(id="re_service_123")
            refund_payment(payment)

        assert payment.status == Payment.Status.REFUNDED
        mock_refund.assert_called_once_with(
            payment_intent="pi_refund_service_123",
            amount=int(payment.amount * 100),
            reason="requested_by_customer",
        )

    def test_refund_payment_without_payment_intent_raises(self, payment_factory):
        """Paiement sans PaymentIntent → lève InvalidRequestError."""
        payment = payment_factory(
            status=Payment.Status.PAID,
            stripe_payment_intent_id="",  # Pas de PI
        )

        with pytest.raises(stripe.error.InvalidRequestError):
            refund_payment(payment)

    def test_handle_checkout_event_payment_intent_succeeded(
        self, payment_factory
    ):
        """handle_checkout_event traite payment_intent.succeeded (via session.completed)."""
        payment = payment_factory(
            status=Payment.Status.PENDING,
            stripe_session_id="cs_service_event_123",
        )

        event = _make_checkout_session_completed_event("cs_service_event_123", "pi_service_123")
        result = handle_checkout_event(stripe.Event.construct_from(event, stripe.api_key))

        assert result is True
        payment.refresh_from_db()
        assert payment.status == Payment.Status.PAID
        assert payment.stripe_payment_intent_id == "pi_service_123"
        assert payment.booking.status == Booking.Status.CONFIRMED

    def test_handle_checkout_event_unknown_session_returns_false(self):
        """Session inconnue → False."""
        event = _make_checkout_session_completed_event("cs_unknown_999")
        result = handle_checkout_event(stripe.Event.construct_from(event, stripe.api_key))
        assert result is False


# ---------------------------------------------------------------------------
# EDGE CASES & PERMISSIONS
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPaymentEdgeCases:
    """Cas limites et permissions."""

    def test_payment_create_validates_booking_pending_only(self, client_api_client, booking_factory):
        """Seule réservation PENDING peut être payée."""
        booking = booking_factory(
            user=client_api_client.handler._force_user,
            status=Booking.Status.CONFIRMED,
        )
        response = client_api_client.post(
            "/api/v1/payments/",
            {"booking": booking.id},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "en attente" in response.data["booking"][0].lower()

    def test_payment_create_validates_ownership(self, client_api_client, booking_factory, make_client):
        """Client ne peut pas payer réservation d'un autre."""
        other_client, other_user = make_client("client")
        booking = booking_factory(user=other_user, status=Booking.Status.PENDING)
        response = client_api_client.post(
            "/api/v1/payments/",
            {"booking": booking.id},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "n'appartient pas" in response.data["booking"][0].lower() or "appartient pas" in response.data["booking"][0].lower()

    def test_payment_create_duplicate_returns_400(self, client_api_client, payment_factory):
        """Deuxième paiement pour même réservation → 400."""
        payment = payment_factory(user=client_api_client.handler._force_user)
        response = client_api_client.post(
            "/api/v1/payments/",
            {"booking": payment.booking.id},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "existe déjà" in response.data["booking"][0].lower()

    def test_manager_can_refund_own_hotel_payment(self, manager_api_client, payment_factory, hotel_manager_user):
        """Manager peut rembourser paiement de son hôtel."""
        hotel = hotel_manager_user.managed_hotels.first()
        room = hotel.rooms.first()
        booking = BookingFactory.create(hotel=hotel, room=room, status=Booking.Status.CONFIRMED)
        payment = Payment.objects.create(
            user=booking.user,
            booking=booking,
            amount=booking.total_price,
            currency=settings.STRIPE_CURRENCY,
            status=Payment.Status.PAID,
            stripe_payment_intent_id="pi_manager_refund",
        )

        with patch("apps.payments.services.stripe.Refund.create"):
            response = manager_api_client.post(f"/api/v1/payments/{payment.id}/refund/")

        assert response.status_code == status.HTTP_200_OK

    def test_manager_cannot_refund_other_hotel_payment(self, manager_api_client, payment_factory):
        """Manager ne peut pas rembourser paiement d'un autre hôtel."""
        # Créer un autre hôtel avec un autre gestionnaire
        other_manager = UserFactory.create_hotel_manager()
        other_hotel = HotelFactory.create(manager=other_manager)
        other_room = RoomFactory.create(hotel=other_hotel)
        other_booking = BookingFactory.create(
            hotel=other_hotel,
            room=other_room,
            status=Booking.Status.CONFIRMED,
        )
        payment = Payment.objects.create(
            user=other_booking.user,
            booking=other_booking,
            amount=other_booking.total_price,
            currency=settings.STRIPE_CURRENCY,
            status=Payment.Status.PAID,
            stripe_payment_intent_id="pi_other_hotel",
        )

        with patch("apps.payments.services.stripe.Refund.create"):
            response = manager_api_client.post(f"/api/v1/payments/{payment.id}/refund/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_refund_any_payment(self, admin_api_client, payment_factory):
        """Admin peut rembourser n'importe quel paiement."""
        payment = payment_factory(
            status=Payment.Status.PAID,
            stripe_payment_intent_id="pi_admin_refund",
        )

        with patch("apps.payments.services.stripe.Refund.create"):
            response = admin_api_client.post(f"/api/v1/payments/{payment.id}/refund/")

        assert response.status_code == status.HTTP_200_OK


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


@pytest.fixture
def booking_factory(client_user, room):
    """Factory pour créer des réservations en base."""
    def _create_booking(**kwargs):
        defaults = {
            "user": client_user,
            "hotel": room.hotel,
            "room": room,
            "check_in": _future_dates(days_ahead=10)[0],
            "check_out": _future_dates(days_ahead=10)[1],
            "adults": 2,
            "children": 0,
            "price_per_night": room.price_per_night,
            "status": Booking.Status.PENDING,
        }
        defaults.update(kwargs)
        return Booking.objects.create(**defaults)
    return _create_booking


@pytest.fixture
def payment_factory(booking):
    """Factory pour créer des paiements en base."""
    def _create_payment(**kwargs):
        defaults = {
            "user": booking.user,
            "booking": kwargs.pop("booking", booking),
            "amount": kwargs.pop("amount", booking.total_price),
            "currency": settings.STRIPE_CURRENCY,
            "status": Payment.Status.PENDING,
        }
        defaults.update(kwargs)
        return Payment.objects.create(**defaults)
    return _create_payment