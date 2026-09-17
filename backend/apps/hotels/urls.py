"""URLs de l'API : hôtels, chambres, équipements, favoris."""

from rest_framework.routers import DefaultRouter

from apps.hotels.views import AmenityViewSet, FavoriteViewSet, HotelViewSet, RoomViewSet

router = DefaultRouter()
router.register("hotels", HotelViewSet, basename="hotel")
router.register("rooms", RoomViewSet, basename="room")
router.register("amenities", AmenityViewSet, basename="amenity")
router.register("favorites", FavoriteViewSet, basename="favorite")

urlpatterns = router.urls