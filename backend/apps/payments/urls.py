"""URLs de l'API : paiements."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.payments.views import PaymentViewSet, StripeWebhookView

router = DefaultRouter()
router.register("payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("payments/webhook/", StripeWebhookView.as_view(), name="payment-webhook"),
] + router.urls