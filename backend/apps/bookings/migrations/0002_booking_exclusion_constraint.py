"""Contrainte d'exclusion PostgreSQL anti double-réservation.

Garantit au niveau de la base de données qu'une chambre ne peut pas être
réservée deux fois sur des périodes qui se chevauchent (statuts actifs :
``pending`` et ``confirmed``).

Migration volontairement no-op sur les autres moteurs (par ex. SQLite en
développement) pour rester portable. La validation applicative
(``Booking.clean``) reste active partout.
"""

from django.db import migrations

EXCLUSION_CONSTRAINT_NAME = "booking_no_overlap_active"


def create_exclusion_constraint(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")
        cursor.execute(
            f"""
            ALTER TABLE bookings_booking
            ADD CONSTRAINT {EXCLUSION_CONSTRAINT_NAME}
            EXCLUDE USING gist (
                room_id WITH =,
                daterange(check_in, check_out, '[)') WITH &&
            )
            WHERE (status IN ('pending', 'confirmed'));
            """
        )


def drop_exclusion_constraint(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f"ALTER TABLE bookings_booking "
            f"DROP CONSTRAINT IF EXISTS {EXCLUSION_CONSTRAINT_NAME};"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            create_exclusion_constraint, drop_exclusion_constraint
        ),
    ]