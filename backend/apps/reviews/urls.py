"""URLs de l'API : avis clients."""

from rest_framework.routers import DefaultRouter

from apps.reviews.views import ReviewViewSet

router = DefaultRouter()
router.register("reviews", ReviewViewSet, basename="review")

urlpatterns = router.urls