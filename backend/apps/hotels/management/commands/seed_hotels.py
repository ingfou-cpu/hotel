"""Management command to seed hotels with gallery images, rooms, and room images."""

import os
from decimal import Decimal

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.hotels.models import Hotel, HotelImage, Room, RoomImage


STAGING_DIR = r"C:\Users\ADMINI~1\AppData\Local\Temp\opencode\hotelseed"
ROOMS_STAGING_DIR = os.path.join(STAGING_DIR, "rooms")

HOTELS_DATA = [
    {
        "name": "Riad Al Assil",
        "city": "Marrakech",
        "country": "Maroc",
        "stars": 5,
        "latitude": Decimal("31.629472"),
        "longitude": Decimal("-7.981103"),
        "address": "12 Derb Sidi Bouloukat, Médina",
        "description": (
            "Riad traditionnel au cœur de la médina de Marrakech, autour d'un patio orné "
            "de zelliges et d'une fontaine. Terrasse panoramique, salon marocain et calme "
            "absolu à quelques minutes des souks."
        ),
        "images": [
            {
                "filename": "marrakech_1.jpg",
                "alt": "Patio du Riad Al Assil avec fontaine centrale",
                "is_primary": True,
            },
            {
                "filename": "marrakech_2.jpg",
                "alt": "Cour intérieure du riad décorée de zelliges",
                "is_primary": False,
            },
        ],
        "rooms": [
            {
                "room_number": "R01",
                "room_type": "double",
                "price_per_night": Decimal("120.00"),
                "max_occupancy": 2,
                "beds": 1,
                "description": "Chambre double donnant sur le patio bleu",
            },
            {
                "room_number": "R02",
                "room_type": "suite",
                "price_per_night": Decimal("220.00"),
                "max_occupancy": 3,
                "beds": 2,
                "description": "Suite avec salon marocain et terrasse privée",
            },
            {
                "room_number": "R03",
                "room_type": "family",
                "price_per_night": Decimal("260.00"),
                "max_occupancy": 4,
                "beds": 3,
                "description": "Suite familiale au calme de la médina",
            },
        ],
        "room_pics": {
            "R01": {"filename": "riad_room_1.jpg", "alt": "Chambre double au charme traditionnel"},
            "R02": {"filename": "riad_room_2.jpg", "alt": "Suite du riad aux tons fleuris"},
            "R03": {"filename": "riad_room_3.jpg", "alt": "Grande chambre familiale à la marocaine"},
        },
    },
    {
        "name": "Hôtel Saint-Germain",
        "city": "Paris",
        "country": "France",
        "stars": 4,
        "latitude": Decimal("48.853600"),
        "longitude": Decimal("2.333900"),
        "address": "17 rue Lobineau, 75006 Paris",
        "description": (
            "Maison de charme dans le quartier Saint-Germain-des-Prés, façade haussmannienne "
            "et esprit bohème. À deux pas du Jardin du Luxembourg et des galeries d'art de la "
            "rive gauche."
        ),
        "images": [
            {
                "filename": "paris_1.jpg",
                "alt": "Façade haussmannienne de l'Hôtel Saint-Germain",
                "is_primary": True,
            },
            {
                "filename": "paris_2.jpg",
                "alt": "Entrée lumineuse et élégante de l'hôtel",
                "is_primary": False,
            },
        ],
        "rooms": [
            {
                "room_number": "101",
                "room_type": "single",
                "price_per_night": Decimal("140.00"),
                "max_occupancy": 1,
                "beds": 1,
                "description": "Chambre single élégante vue cour",
            },
            {
                "room_number": "102",
                "room_type": "double",
                "price_per_night": Decimal("180.00"),
                "max_occupancy": 2,
                "beds": 1,
                "description": "Chambre double haussmannienne",
            },
            {
                "room_number": "103",
                "room_type": "suite",
                "price_per_night": Decimal("340.00"),
                "max_occupancy": 3,
                "beds": 2,
                "description": "Suite avec salon et vue sur les toits de Paris",
            },
        ],
        "room_pics": {
            "101": {"filename": "paris_room_1.jpg", "alt": "Chambre single élégante, lumière douce"},
            "102": {"filename": "paris_room_2.jpg", "alt": "Chambre double raffinée, esprit parisien"},
            "103": {"filename": "paris_room_3.jpg", "alt": "Suite avec salon contemporain"},
        },
    },
    {
        "name": "Hôtel Alpenblick",
        "city": "Zermatt",
        "country": "Suisse",
        "stars": 4,
        "latitude": Decimal("46.020700"),
        "longitude": Decimal("7.749100"),
        "address": "Kleine Scheidegg 3816, Zermatt",
        "description": (
            "Grand hôtel de montagne du XIXe siècle perché à 2 070 m d'altitude, face à la "
            "Jungfrau et à l'Eiger. Panorama exceptionnel, spa alpin et accès direct aux pistes "
            "et aux trains de la Jungfraubahn."
        ),
        "images": [
            {
                "filename": "zermatt_1.jpg",
                "alt": "Grand chalet alpin de l'Hôtel Alpenblick devant les sommets",
                "is_primary": True,
            },
            {
                "filename": "zermatt_2.jpg",
                "alt": "Les hôtels de Kleine Scheidegg sous la Jungfrau",
                "is_primary": False,
            },
        ],
        "rooms": [
            {
                "room_number": "201",
                "room_type": "double",
                "price_per_night": Decimal("250.00"),
                "max_occupancy": 2,
                "beds": 1,
                "description": "Chambre double face à la Jungfrau",
            },
            {
                "room_number": "202",
                "room_type": "suite",
                "price_per_night": Decimal("420.00"),
                "max_occupancy": 3,
                "beds": 2,
                "description": "Suite panoramique avec bain à remous",
            },
            {
                "room_number": "203",
                "room_type": "family",
                "price_per_night": Decimal("480.00"),
                "max_occupancy": 5,
                "beds": 3,
                "description": "Chambre familiale au pied des pistes",
            },
        ],
        "room_pics": {
            "201": {"filename": "alpen_room_1.jpg", "alt": "Chambre double chaleureuse en bois"},
            "202": {"filename": "alpen_room_2.jpg", "alt": "Suite historique face à l'Eiger"},
            "203": {"filename": "alpen_room_3.jpg", "alt": "Chambre familiale spacieuse en Suisse"},
        },
    },
    {
        "name": "Hôtel Riviera Bleue",
        "city": "Nice",
        "country": "France",
        "stars": 5,
        "latitude": Decimal("43.695400"),
        "longitude": Decimal("7.258900"),
        "address": "37 promenade des Anglais, 06000 Nice",
        "description": (
            "Palace Belle Époque face à la baie des Anges, coupole rose mythique et plage "
            "privée. Restaurant étoilé, bar lounge et service de conciergerie dédié."
        ),
        "images": [
            {
                "filename": "nice_1.jpg",
                "alt": "Façade Belle Époque de l'Hôtel Riviera Bleue",
                "is_primary": True,
            },
            {
                "filename": "nice_2.jpg",
                "alt": "Vue de l'hôtel depuis la plage des Anglais",
                "is_primary": False,
            },
        ],
        "rooms": [
            {
                "room_number": "301",
                "room_type": "double",
                "price_per_night": Decimal("320.00"),
                "max_occupancy": 2,
                "beds": 1,
                "description": "Chambre double vue baie des Anges",
            },
            {
                "room_number": "302",
                "room_type": "suite",
                "price_per_night": Decimal("580.00"),
                "max_occupancy": 3,
                "beds": 2,
                "description": "Suite Belle Époque avec balcon",
            },
            {
                "room_number": "303",
                "room_type": "family",
                "price_per_night": Decimal("620.00"),
                "max_occupancy": 4,
                "beds": 3,
                "description": "Suite familiale face à la mer",
            },
        ],
        "room_pics": {
            "301": {"filename": "sea_room_1.jpg", "alt": "Chambre double avec vue mer"},
            "302": {"filename": "sea_room_2.jpg", "alt": "Suite panoramique ouvrant sur la mer"},
            "303": {"filename": "sea_room_3.jpg", "alt": "Chambre familiale moderne, vue côtière"},
        },
    },
    {
        "name": "Piccadilly Grand Hotel",
        "city": "London",
        "country": "Royaume-Uni",
        "stars": 5,
        "latitude": Decimal("51.507400"),
        "longitude": Decimal("-0.138600"),
        "address": "Carlton Street, Mayfair, London W1K 2EH",
        "description": (
            "Hôtel de luxe édouardien au cœur de Mayfair, entre Piccadilly et Berkeley Square. "
            "Salons boisés, afternoon tea réputé et suites au raffinement britannique."
        ),
        "images": [
            {
                "filename": "london_1.jpg",
                "alt": "Façade édouardienne du Piccadilly Grand Hotel",
                "is_primary": True,
            },
            {
                "filename": "london_2.jpg",
                "alt": "Mayfair et l'angle historique de l'hôtel",
                "is_primary": False,
            },
        ],
        "rooms": [
            {
                "room_number": "401",
                "room_type": "double",
                "price_per_night": Decimal("290.00"),
                "max_occupancy": 2,
                "beds": 1,
                "description": "Chambre double élégante",
            },
            {
                "room_number": "402",
                "room_type": "suite",
                "price_per_night": Decimal("550.00"),
                "max_occupancy": 3,
                "beds": 2,
                "description": "Suite édouardienne avec salon",
            },
            {
                "room_number": "403",
                "room_type": "family",
                "price_per_night": Decimal("600.00"),
                "max_occupancy": 4,
                "beds": 3,
                "description": "Suite familiale sur Mayfair",
            },
        ],
        "room_pics": {
            "401": {"filename": "london_room_1.jpg", "alt": "Chambre double élégante de Mayfair"},
            "402": {"filename": "london_room_2.jpg", "alt": "Suite au raffinement édouardien"},
            "403": {"filename": "london_room_3.jpg", "alt": "Chambre familiale confortable"},
        },
    },
    {
        "name": "Palazzo Aurelia",
        "city": "Rome",
        "country": "Italie",
        "stars": 5,
        "latitude": Decimal("41.886000"),
        "longitude": Decimal("12.470300"),
        "address": "Viale delle Mura Aurelie 18, 00165 Rome",
        "description": (
            "Palace italien au charme néo-classique, le long des murs auréliens à deux pas "
            "du Trastevere. Façade noble, cour intérieure ombragée, piscine panoramique et "
            "hospitalité romaine raffinée."
        ),
        "images": [
            {
                "filename": "rome_1.jpg",
                "alt": "Façade contemporaine du Palazzo Aurelia",
                "is_primary": True,
            },
            {
                "filename": "rome_2.jpg",
                "alt": "Piscine extérieure et espace lounge de l'hôtel",
                "is_primary": False,
            },
        ],
        "rooms": [
            {
                "room_number": "501",
                "room_type": "double",
                "price_per_night": Decimal("260.00"),
                "max_occupancy": 2,
                "beds": 1,
                "description": "Chambre double lumineuse vue cour",
            },
            {
                "room_number": "502",
                "room_type": "suite",
                "price_per_night": Decimal("480.00"),
                "max_occupancy": 3,
                "beds": 2,
                "description": "Suite romaine avec salon et coin bureau",
            },
            {
                "room_number": "503",
                "room_type": "family",
                "price_per_night": Decimal("540.00"),
                "max_occupancy": 4,
                "beds": 3,
                "description": "Suite familiale spacieuse près de la piscine",
            },
        ],
        "room_pics": {
            "501": {"filename": "rome_room_1.jpg", "alt": "Chambre double claire et cosy"},
            "502": {"filename": "rome_room_2.jpg", "alt": "Suite avec lit king-size et salon"},
            "503": {"filename": "rome_room_3.jpg", "alt": "Chambre familiale contemporaine"},
        },
    },
]


class Command(BaseCommand):
    """Seed 5 hotels with 2 gallery images, 3 rooms each, and 1 primary photo per room."""

    help = "Seed 5 hotels with gallery images, rooms, and room images (idempotent)"

    def handle(self, *args, **options):
        with transaction.atomic():
            for hotel_data in HOTELS_DATA:
                images_data = hotel_data.get("images", [])
                rooms_data = hotel_data.get("rooms", [])
                room_pics = hotel_data.get("room_pics", {})

                hotel, created = Hotel.objects.get_or_create(
                    name=hotel_data["name"],
                    city=hotel_data["city"],
                    defaults={k: v for k, v in hotel_data.items() if k in {
                        "name", "city", "country", "stars", "latitude",
                        "longitude", "address", "description",
                    }},
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created hotel: {hotel.name} ({hotel.city}) - ID: {hotel.id}"
                        )
                    )
                    self._create_images(hotel, images_data)
                    self._create_rooms(hotel, rooms_data, room_pics)
                else:
                    existing_images = hotel.images.count()
                    if existing_images == 0:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Hotel exists but has no images: {hotel.name} ({hotel.city}) - ID: {hotel.id}"
                            )
                        )
                        self._create_images(hotel, images_data)
                    else:
                        self.stdout.write(
                            self.style.NOTICE(
                                f"Hotel already exists with {existing_images} images, skipping: "
                                f"{hotel.name} ({hotel.city}) - ID: {hotel.id}"
                            )
                        )

                    existing_rooms = hotel.rooms.count()
                    if existing_rooms == 0:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Hotel exists but has no rooms: {hotel.name} ({hotel.city}) - ID: {hotel.id}"
                            )
                        )
                        self._create_rooms(hotel, rooms_data, room_pics)
                    else:
                        self.stdout.write(
                            self.style.NOTICE(
                                f"Hotel already has {existing_rooms} rooms, checking room images: "
                                f"{hotel.name} ({hotel.city}) - ID: {hotel.id}"
                            )
                        )
                        # Check and create room images for existing rooms
                        for room in hotel.rooms.all():
                            if room.images.count() == 0:
                                room_number = room.room_number
                                if room_number in room_pics:
                                    self._create_room_images(room, [room_pics[room_number]])

    def _create_images(self, hotel, images_data):
        """Create HotelImage entries for a hotel."""
        for img_data in images_data:
            filepath = os.path.join(STAGING_DIR, img_data["filename"])
            if not os.path.exists(filepath):
                self.stdout.write(
                    self.style.ERROR(f"Source image not found: {filepath}")
                )
                continue

            with open(filepath, "rb") as f:
                django_file = File(f, name=img_data["filename"])
                HotelImage.objects.create(
                    hotel=hotel,
                    image=django_file,
                    alt=img_data["alt"],
                    is_primary=img_data["is_primary"],
                )
            self.stdout.write(
                f"  Added image: {img_data['filename']} (primary={img_data['is_primary']})"
            )

    def _create_rooms(self, hotel, rooms_data, room_pics):
        """Create Room entries for a hotel (idempotent) and their images."""
        for room_data in rooms_data:
            room_number = room_data["room_number"]
            room, created = Room.objects.get_or_create(
                hotel=hotel,
                room_number=room_number,
                defaults=room_data,
            )
            if created:
                self.stdout.write(
                    f"  Created room: {room_number} ({room.room_type}) - "
                    f"{room.price_per_night}€/night"
                )
            else:
                self.stdout.write(
                    f"  Room already exists: {room_number} - checking images"
                )

            # Create room images if room has no images and we have pic data for it
            if room.images.count() == 0 and room_number in room_pics:
                self._create_room_images(room, [room_pics[room_number]])

    def _create_room_images(self, room, pics_data):
        """Create RoomImage entries for a room."""
        for pic_data in pics_data:
            filepath = os.path.join(ROOMS_STAGING_DIR, pic_data["filename"])
            if not os.path.exists(filepath):
                self.stdout.write(
                    self.style.ERROR(f"Source room image not found: {filepath}")
                )
                continue

            with open(filepath, "rb") as f:
                django_file = File(f, name=pic_data["filename"])
                RoomImage.objects.create(
                    room=room,
                    image=django_file,
                    alt=pic_data["alt"],
                    is_primary=True,
                )
            self.stdout.write(
                f"    Added room image: {pic_data['filename']} (primary=True)"
            )