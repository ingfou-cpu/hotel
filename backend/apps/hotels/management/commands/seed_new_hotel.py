"""Management command to seed a single new hotel with photos and a room (idempotent)."""

import io
import os
import random
import urllib.request
from decimal import Decimal

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image

from apps.hotels.models import Hotel, HotelImage, Room, RoomImage


def _download_image(url, referer="https://images.pexels.com/"):
    """Download image from URL with browser headers. Returns bytes or None on failure."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": referer,
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read()
    except Exception as e:
        return None


def _generate_placeholder(width=1200, height=800, color=None):
    """Generate a colored JPEG placeholder in memory."""
    if color is None:
        color = (
            random.randint(100, 200),
            random.randint(100, 200),
            random.randint(100, 200),
        )
    img = Image.new("RGB", (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    return buffer.read()


class Command(BaseCommand):
    """Seed one new hotel with gallery images, one room, and room image (idempotent)."""

    help = "Seed Riad Tamarin d'Or hotel with images and a Suite Deluxe room (idempotent)"

    def handle(self, *args, **options):
        with transaction.atomic():
            hotel_data = {
                "name": "Riad Tamarin d'Or",
                "city": "Marrakech",
                "country": "Maroc",
                "stars": 5,
                "latitude": Decimal("31.6302"),
                "longitude": Decimal("-7.9897"),
                "address": "12 Derb el Ferrane, Médina, Marrakech",
                "description": (
                    "Un riad d'exception au cœur de la médina de Marrakech, mêlant zellige ancien, "
                    "patio ombragé et piscine privée. Séjournez à deux pas des souks dans une "
                    "demeure entièrement restaurée."
                ),
                "is_active": True,
            }

            images_data = [
                {
                    "url": "https://images.pexels.com/photos/15531322/pexels-photo-15531322.jpeg?auto=compress&cs=tinysrgb&w=1920",
                    "alt": "Riad Tamarin d'Or — cour intérieure et patio",
                    "is_primary": True,
                    "filename": "riad_tamarin_cour.jpg",
                },
                {
                    "url": "https://images.pexels.com/photos/38127493/pexels-photo-38127493.jpeg?auto=compress&cs=tinysrgb&w=1920",
                    "alt": "Riad Tamarin d'Or — piscine privée",
                    "is_primary": False,
                    "filename": "riad_tamarin_piscine.jpg",
                },
                {
                    "url": "https://pixabay.com/get/ge93955851b7353befcbe5a2a1a83a39a9ecf25b9f7410bfc61648e4cb3bcd8b59f340fbabd5c4c0149a286bf49f25d6ba7121f482cd1f4671afeadd6fea82147_1280.jpg",
                    "alt": "Riad Tamarin d'Or — suite deluxe",
                    "is_primary": False,
                    "filename": "riad_tamarin_suite.jpg",
                },
            ]

            room_data = {
                "room_number": "S01",
                "room_type": "suite",
                "price_per_night": Decimal("3200.00"),
                "max_occupancy": 3,
                "beds": 2,
                "description": "Suite Deluxe avec patio privé, salon marocain, lit king-size et salle de bain en tadelakt. Vue sur la cour intérieure et la piscine.",
                "is_available": True,
                "is_active": True,
            }

            hotel, created = Hotel.objects.get_or_create(
                name=hotel_data["name"],
                city=hotel_data["city"],
                defaults=hotel_data,
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created hotel: {hotel.name} ({hotel.city}) - ID: {hotel.id}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.NOTICE(
                        f"Hotel already exists: {hotel.name} ({hotel.city}) - ID: {hotel.id}"
                    )
                )

            # Create hotel images
            for img_data in images_data:
                # Check if image with this alt already exists for this hotel
                if HotelImage.objects.filter(hotel=hotel, alt=img_data["alt"]).exists():
                    self.stdout.write(
                        self.style.NOTICE(f"  Image already exists: {img_data['alt']}")
                    )
                    continue

                self.stdout.write(f"  Downloading: {img_data['url']}")
                image_bytes = _download_image(img_data["url"])

                if image_bytes is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Download failed for {img_data['url']}, generating placeholder"
                        )
                    )
                    image_bytes = _generate_placeholder()
                    img_data["filename"] = f"placeholder_{img_data['filename']}"

                # Create the HotelImage
                django_file = File(
                    io.BytesIO(image_bytes),
                    name=img_data["filename"],
                )
                HotelImage.objects.create(
                    hotel=hotel,
                    image=django_file,
                    alt=img_data["alt"],
                    is_primary=img_data["is_primary"],
                )
                self.stdout.write(
                    f"  Added image: {img_data['filename']} (primary={img_data['is_primary']})"
                )

            # Create room (idempotent by hotel + room_number)
            room, room_created = Room.objects.get_or_create(
                hotel=hotel,
                room_number=room_data["room_number"],
                defaults=room_data,
            )

            if room_created:
                self.stdout.write(
                    f"  Created room: {room.room_number} ({room.room_type}) - "
                    f"{room.price_per_night} MAD/night"
                )
            else:
                self.stdout.write(
                    self.style.NOTICE(f"  Room already exists: {room.room_number}")
                )

            # Create room image (use the suite photo as room image)
            if room.images.count() == 0:
                suite_img_data = images_data[2]  # The suite deluxe photo
                if not RoomImage.objects.filter(room=room).exists():
                    self.stdout.write(f"  Downloading room image: {suite_img_data['url']}")
                    image_bytes = _download_image(suite_img_data["url"])

                    if image_bytes is None:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Download failed for {suite_img_data['url']}, generating placeholder"
                            )
                        )
                        image_bytes = _generate_placeholder()
                        suite_img_data["filename"] = f"placeholder_{suite_img_data['filename']}"

                    django_file = File(
                        io.BytesIO(image_bytes),
                        name=suite_img_data["filename"],
                    )
                    RoomImage.objects.create(
                        room=room,
                        image=django_file,
                        alt=suite_img_data["alt"],
                        is_primary=True,
                    )
                    self.stdout.write(
                        f"  Added room image: {suite_img_data['filename']} (primary=True)"
                    )

            self.stdout.write(self.style.SUCCESS("Done."))