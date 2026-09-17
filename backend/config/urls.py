"""Configuration des URLs racine du projet HotelBooking."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Documentation API (OpenAPI 3)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # API versionnée
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.hotels.urls")),
    path("api/v1/", include("apps.bookings.urls")),
    path("api/v1/", include("apps.payments.urls")),
    path("api/v1/", include("apps.reviews.urls")),
    path("api/v1/", include("apps.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)