"""
Django management command to bulk-create users in GeoNode.

INSTALL
-------
Drop this file into any GeoNode app's management/commands package, e.g.:

    geonode/people/management/commands/create_bulk_users.py

(create the `management/` and `management/commands/` dirs with empty
__init__.py files if they don't already exist).

USAGE (from the GeoNode project root, inside your venv / container)
---------------------------------------------------------------------
    python manage.py create_bulk_users --count 1000 --prefix testuser \
        --domain example.com --group public --csv-out generated_users.csv

Common options:
    --count       N        how many users to create (default 1000)
    --start       N        starting numeric suffix (default 1) -> testuser1, testuser2, ...
    --prefix      STR      username/email prefix (default "user")
    --domain      STR      email domain, e.g. example.com (default "example.com")
    --password    STR      fixed password for all users; if omitted, a random
                            password is generated per user
    --group       STR      name of an existing Django/GeoNode Group to add every
                            user to (skipped if not given or not found)
    --active      BOOL     mark users active immediately (default true)
    --csv-out     PATH     where to write username,email,password (default
                            generated_users.csv in current directory)
    --dry-run              don't write anything, just show what would happen

The command is idempotent: usernames/emails that already exist are skipped
(reported at the end), so you can safely re-run it if it fails partway
through or you want to top up to a larger count later.
"""

import csv
import random
import string

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()


def random_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = "Bulk-create GeoNode users for load testing / seeding."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=1000)
        parser.add_argument("--start", type=int, default=1)
        parser.add_argument("--prefix", type=str, default="user")
        parser.add_argument("--domain", type=str, default="example.com")
        parser.add_argument("--password", type=str, default=None)
        parser.add_argument("--group", type=str, default=None)
        parser.add_argument("--active", type=lambda v: v.lower() != "false", default=True)
        parser.add_argument("--csv-out", type=str, default="generated_users.csv")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        count = opts["count"]
        start = opts["start"]
        prefix = opts["prefix"]
        domain = opts["domain"]
        fixed_password = opts["password"]
        group_name = opts["group"]
        active = opts["active"]
        csv_out = opts["csv_out"]
        dry_run = opts["dry_run"]

        group = None
        if group_name:
            group = Group.objects.filter(name=group_name).first()
            if not group:
                self.stdout.write(self.style.WARNING(
                    f"Group '{group_name}' not found — users will be created without a group."
                ))

        created, skipped = [], []

        rows_to_write = []

        with transaction.atomic():
            for i in range(start, start + count):
                username = f"{prefix}{i}"
                email = f"{prefix}{i}@{domain}"

                if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
                    skipped.append(username)
                    continue

                password = fixed_password or random_password()

                if not dry_run:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                    )
                    user.is_active = active
                    user.save(update_fields=["is_active"])
                    if group:
                        user.groups.add(group)

                created.append(username)
                rows_to_write.append((username, email, password))

                if len(created) % 100 == 0:
                    self.stdout.write(f"...{len(created)} users created so far")

            if dry_run:
                # roll back — nothing should be persisted in a dry run
                transaction.set_rollback(True)

        if not dry_run and rows_to_write:
            with open(csv_out, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["username", "email", "password"])
                writer.writerows(rows_to_write)
            self.stdout.write(self.style.SUCCESS(f"Wrote credentials for {len(rows_to_write)} users to {csv_out}"))

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created: {len(created)}, Skipped (already existed): {len(skipped)}"
        ))
        if skipped:
            self.stdout.write(f"Skipped usernames: {', '.join(skipped[:20])}"
                               + (" ..." if len(skipped) > 20 else ""))
