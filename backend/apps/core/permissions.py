"""Permissions métier partagées entre les apps."""

from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.accounts.models import User


class IsHotelManagerOrStaff(BasePermission):
    """Écriture réservée aux gestionnaires d'hôtels et au staff ; lecture ouverte."""

    message = "Réservé aux gestionnaires d'hôtels."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_staff or user.role == User.Role.HOTEL_MANAGER)
        )


class IsManagerOfHotelOrStaff(BasePermission):
    """Object-level : le gestionnaire propriétaire de l'hôtel (ou le staff).

    Fonctionne sur un ``Hotel`` ou sur une ``Room`` (via ``obj.hotel``).
    """

    message = "Vous devez être le gestionnaire de cet hôtel."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if user.is_staff:
            return True
        hotel = getattr(obj, "hotel", obj)
        return hotel.manager_id == user.id


class IsOwnerOrReadOnly(BasePermission):
    """Object-level : seuls le propriétaire (et le staff) modifient le contenu."""

    message = "Vous ne pouvez modifier que votre propre contenu."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_staff:
            return True
        return obj.user_id == user.id