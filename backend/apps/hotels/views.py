"""Vues de l'API : hôtels, chambres, équipements et favoris."""

from django.db.models import Min, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.core.permissions import (
    IsHotelManagerOrStaff,
    IsManagerOfHotelOrStaff,
)
from apps.hotels.models import Amenity, Favorite, Hotel, Room
from apps.hotels.serializers import (
    AmenitySerializer,
    FavoriteSerializer,
    HotelListSerializer,
    HotelSerializer,
    RoomSerializer,
)


class AmenityViewSet(viewsets.ReadOnlyModelViewSet):
    """Équipements : catalogue en lecture seule."""

    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = ()

    def get_permissions(self):
        # Lecture publique : l'authentification reste possible mais pas requise.
        return []


class HotelViewSet(viewsets.ModelViewSet):
    """Hôtels : catalogue public (recherche + disponibilité) et gestion.

    Recherche : ``?city=&country=&stars=&guests=&check_in=&check_out=``
    Tri : ``?sort=price`` / ``?sort=-price`` / ``?ordering=stars|average_rating``
    Gestionnaire : ``GET /hotels/mine/`` pour ses établissements (y compris inactifs).
    """

    serializer_class = HotelSerializer
    permission_classes = (IsHotelManagerOrStaff, IsManagerOfHotelOrStaff)
    search_fields = ("name", "city", "country", "address")
    ordering_fields = ("stars", "average_rating", "reviews_count", "created_at")

    def get_serializer_class(self):
        if self.action == "list":
            return HotelListSerializer
        return HotelSerializer

    def get_queryset(self):
        user = self.request.user
        params = self.request.query_params

        if self.action == "mine":
            if not (user.is_authenticated):
                return Hotel.objects.none()
            return (
                Hotel.objects.filter(manager=user)
                .select_related("manager")
                .prefetch_related("images")
            )

        qs = Hotel.objects.select_related("manager").prefetch_related("images")

        # Visibilité : actifs pour tous ; un gestionnaire voit aussi les siens,
        # y compris inactifs (pour réactiver depuis l'API).
        if self.action in ("retrieve", "update", "partial_update", "destroy"):
            if user.is_authenticated and user.is_staff:
                pass
            elif user.is_authenticated and user.role == User.Role.HOTEL_MANAGER:
                qs = qs.filter(Q(is_active=True) | Q(manager=user))
            else:
                qs = qs.filter(is_active=True)
        else:
            qs = qs.filter(is_active=True)

        # --- Filtres de recherche (liste) -----------------------------------
        city = params.get("city")
        if city:
            qs = qs.filter(city__icontains=city)
        country = params.get("country")
        if country:
            qs = qs.filter(country__icontains=country)
        stars = params.get("stars")
        if stars:
            qs = qs.filter(stars__gte=stars)

        guests = params.get("guests")
        if guests:
            qs = qs.filter(rooms__max_occupancy__gte=guests)

        # Disponibilité : au moins une chambre libre sur la période.
        check_in = params.get("check_in")
        check_out = params.get("check_out")
        if check_in and check_out:
            occupied = (
                Booking.objects.active()
                .filter(check_in__lt=check_out, check_out__gt=check_in)
                .values_list("room_id", flat=True)
            )
            free_room_hotels = (
                Room.objects.filter(is_active=True, is_available=True)
                .exclude(id__in=occupied)
                .values_list("hotel_id", flat=True)
                .distinct()
            )
            qs = qs.filter(id__in=free_room_hotels)

        # Tri particulier : prix le plus bas des chambres actives.
        sort = params.get("sort")
        if sort in ("price", "-price"):
            direction = "-" if sort.startswith("-") else ""
            qs = qs.filter(rooms__is_active=True).annotate(
                _min_price=Min("rooms__price_per_night")
            ).order_by(f"{direction}_min_price")

        return qs.distinct()

    @action(detail=False, methods=["get"], url_path="mine")
    @extend_schema(
        summary="Mes hôtels (gestionnaire)",
        responses={200: HotelListSerializer(many=True)},
    )
    def mine(self, request, *args, **kwargs):
        """Hôtels gérés par le gestionnaire connecté (lecture seule ici)."""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = HotelListSerializer(
            page if page is not None else queryset,
            many=True,
            context=self.get_serializer_context(),
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class RoomViewSet(viewsets.ModelViewSet):
    """Chambres : lecture publique (plus ``?hotel=`` et ``?check_in/check_out``),
    écriture réservée au gestionnaire de l'hôtel."""

    serializer_class = RoomSerializer
    permission_classes = (IsHotelManagerOrStaff, IsManagerOfHotelOrStaff)

    def get_queryset(self):
        params = self.request.query_params
        qs = Room.objects.select_related("hotel").prefetch_related("images", "amenities")

        if self.action == "list":
            qs = qs.filter(is_active=True)
            hotel_id = params.get("hotel")
            if hotel_id:
                qs = qs.filter(hotel_id=hotel_id)
            check_in = params.get("check_in")
            check_out = params.get("check_out")
            if check_in and check_out:
                occupied = (
                    Booking.objects.active()
                    .filter(check_in__lt=check_out, check_out__gt=check_in)
                    .values_list("room_id", flat=True)
                )
                qs = qs.filter(is_available=True).exclude(id__in=occupied)
        else:
            # Écritures : le gestionnaire ne touche que les chambres de ses hôtels.
            user = self.request.user
            if not user.is_staff and user.role == User.Role.HOTEL_MANAGER:
                qs = qs.filter(hotel__manager=user)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        hotel = serializer.validated_data.get("hotel")
        if not (user.is_staff or hotel.manager_id == user.id):
            raise PermissionDenied(
                "Vous devez être le gestionnaire de cet hôtel pour y ajouter une chambre."
            )
        serializer.save()


class FavoriteViewSet(viewsets.ModelViewSet):
    """Favoris de l'utilisateur connecté (liste / ajout / suppression)."""

    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ("get", "post", "delete", "head", "options")

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related("hotel")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)