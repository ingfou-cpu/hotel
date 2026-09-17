"""Administration Django du domaine Hôtels."""

from django.contrib import admin

from apps.hotels.models import Amenity, Favorite, Hotel, HotelImage, Room, RoomImage


class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 0


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 0


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon")
    search_fields = ("name", "slug")


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "country", "stars", "average_rating", "reviews_count", "is_active")
    list_filter = ("is_active", "stars", "city", "country")
    search_fields = ("name", "city", "country", "address")
    list_select_related = ("manager",)
    filter_horizontal = ("amenities",)
    autocomplete_fields = ("manager",)
    inlines = (HotelImageInline,)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "hotel", "room_number", "room_type", "price_per_night",
        "max_occupancy", "beds", "is_available", "is_active",
    )
    list_filter = ("room_type", "is_available", "is_active")
    search_fields = ("hotel__name", "room_number")
    filter_horizontal = ("amenities",)
    inlines = (RoomImageInline,)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "hotel", "created_at")
    search_fields = ("user__email", "hotel__name")