import glob
import os

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Reset specified Django apps by removing migrations and dropping tables"

    def add_arguments(self, parser):
        parser.add_argument(
            "app_labels",
            nargs="+",
            type=str,
            help="Specify one or more app labels to reset",
        )

    def handle(self, *args, **options):
        app_labels = options["app_labels"]

        # Validate apps
        for app_label in app_labels:
            try:
                apps.get_app_config(app_label)
            except LookupError as e:
                raise CommandError(f'App "{app_label}" not found') from e

        self.stdout.write(
            self.style.WARNING(
                f'About to reset the following apps: {", ".join(app_labels)}'
            )
        )

        confirm = input(
            "Are you sure? This will delete all migrations and drop tables [y/N]: "
        )
        if confirm.lower() != "y":
            self.stdout.write(self.style.NOTICE("Operation cancelled."))
            return

        # Step 1: Delete migrations
        self.stdout.write("Removing migrations...")
        for app_label in app_labels:
            migrations_dir = os.path.join(
                apps.get_app_config(app_label).path, "migrations"
            )
            if os.path.exists(migrations_dir):
                # Remove all migration files except __init__.py
                migration_files = glob.glob(os.path.join(migrations_dir, "0*.py"))
                for f in migration_files:
                    os.remove(f)

                # Ensure __init__.py exists
                init_file = os.path.join(migrations_dir, "__init__.py")
                if not os.path.exists(init_file):
                    open(init_file, "a", encoding="utf-8").close()

                self.stdout.write(f"  Removed migrations for {app_label}")

        # Step 2: Clear django_migrations table entries for these apps
        self.stdout.write("Clearing migration history...")
        with connection.cursor() as cursor:
            for app_label in app_labels:
                cursor.execute(
                    "DELETE FROM django_migrations WHERE app = %s", [app_label]
                )
                self.stdout.write(f"  Cleared migration history for {app_label}")

        # Step 3: Drop tables
        self.stdout.write("Dropping tables...")
        with connection.cursor() as cursor:
            # Disable foreign key checks
            if connection.vendor == "mysql":
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            elif connection.vendor == "postgresql":
                cursor.execute("SET CONSTRAINTS ALL DEFERRED;")

            # Drop tables
            for app_label in app_labels:
                app_config = apps.get_app_config(app_label)
                for model in app_config.get_models():
                    table_name = model._meta.db_table
                    try:
                        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                        self.stdout.write(f"  Dropped table {table_name}")
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f"  Failed to drop {table_name}: {e}")
                        )

            # Re-enable foreign key checks
            if connection.vendor == "mysql":
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            elif connection.vendor == "postgresql":
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE;")

        self.stdout.write(
            self.style.SUCCESS(
                """
Reset complete! Next steps:
1. Create new migrations:
   python manage.py makemigrations [app_names]

2. Apply migrations:
   python manage.py migrate

3. Seed data if needed
"""
            )
        )
