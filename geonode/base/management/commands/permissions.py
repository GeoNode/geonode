"""
Django management command to sweep every GeoNode resource and randomly
(re)assign permission levels to a random subset of users.

INSTALL
-------
Drop this file into any GeoNode app's management/commands package, e.g.:

    geonode/base/management/commands/randomize_resource_permissions.py

(create the `management/` and `management/commands/` dirs with empty
__init__.py files if they don't already exist).

WHAT IT DOES
------------
1. Loads every ResourceBase (Datasets, Documents, Maps, GeoApps, ... -
   whatever subtypes exist in your instance) unless --resource-type
   restricts it.
2. Loads the pool of candidate users (active, non-superuser by default).
3. For each resource:
     - picks a random number of users (between --min-users and --max-users)
     - gives each picked user a random permission level (view / download /
       edit / manage, configurable via --levels)
     - always keeps the resource owner at "manage" level so nobody
       accidentally locks the owner out
     - optionally randomizes the anonymous/public access too (--randomize-anonymous)
     - calls resource.set_permissions(perm_spec) to apply it
4. Writes a CSV log of every (resource, user, level) assignment made.

This is meant for load-testing / QA of the permissions system, NOT for
production use — it will overwrite existing sharing settings on every
resource it touches.

USAGE
-----
    python manage.py randomize_resource_permissions --seed 42 \
        --min-users 1 --max-users 5 --csv-out perm_assignments.csv

    # only datasets, only look at first 200, dry run to preview:
    python manage.py randomize_resource_permissions --resource-type dataset \
        --limit 200 --dry-run

Options:
    --resource-type   dataset|document|map|geoapp|all   (default: all)
    --limit           N     only process the first N resources found (default: all)
    --min-users       N     min number of users to touch per resource (default 1)
    --max-users       N     max number of users to touch per resource (default 5)
    --levels          CSV   subset of view,download,edit,manage to sample from
                            (default: view,download,edit,manage)
    --include-superusers   also allow superusers to be picked as random subjects
                            (default: excluded)
    --randomize-anonymous   also randomly flip public/anonymous view access
    --seed            N     random seed, for reproducible runs
    --csv-out         PATH  where to log assignments (default resource_perm_log.csv)
    --dry-run               compute everything but don't call set_permissions()
"""

import csv
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from geonode.base.models import ResourceBase

User = get_user_model()

LEVELS = {
    "view": ["view_resourcebase"],
    "download": ["view_resourcebase", "download_resourcebase"],
    "edit": ["view_resourcebase", "download_resourcebase", "change_resourcebase", "change_resourcebase_metadata"],
    "manage": [
        "view_resourcebase",
        "download_resourcebase",
        "change_resourcebase",
        "change_resourcebase_metadata",
        "change_resourcebase_permissions",
        "delete_resourcebase",
    ],
}

RESOURCE_TYPE_MAP = {
    "dataset": "geonode.layers.models.Dataset",
    "document": "geonode.documents.models.Document",
    "map": "geonode.maps.models.Map",
    "geoapp": "geonode.geoapps.models.GeoApp",
}


def import_class(path):
    module_path, class_name = path.rsplit(".", 1)
    module = __import__(module_path, fromlist=[class_name])
    return getattr(module, class_name)


class Command(BaseCommand):
    help = "Randomly (re)assign permission levels across all GeoNode resources, for load/QA testing."

    def add_arguments(self, parser):
        parser.add_argument("--resource-type", type=str, default="all",
                             choices=["all"] + list(RESOURCE_TYPE_MAP.keys()))
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--min-users", type=int, default=1)
        parser.add_argument("--max-users", type=int, default=5)
        parser.add_argument("--levels", type=str, default="view,download,edit,manage")
        parser.add_argument("--include-superusers", action="store_true")
        parser.add_argument("--randomize-anonymous", action="store_true")
        parser.add_argument("--seed", type=int, default=None)
        parser.add_argument("--csv-out", type=str, default="resource_perm_log.csv")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        if opts["seed"] is not None:
            random.seed(opts["seed"])

        if opts["min_users"] > opts["max_users"]:
            raise CommandError("--min-users cannot be greater than --max-users")

        levels = [lvl.strip() for lvl in opts["levels"].split(",") if lvl.strip()]
        for lvl in levels:
            if lvl not in LEVELS:
                raise CommandError(f"Unknown level '{lvl}'. Valid: {', '.join(LEVELS)}")

        # 1) resources
        if opts["resource_type"] == "all":
            resources = ResourceBase.objects.all()
        else:
            model = import_class(RESOURCE_TYPE_MAP[opts["resource_type"]])
            resources = model.objects.all()

        resources = list(resources.order_by("id"))
        if opts["limit"]:
            resources = resources[: opts["limit"]]

        if not resources:
            self.stdout.write(self.style.WARNING("No resources found — nothing to do."))
            return

        # 2) candidate users
        user_qs = User.objects.filter(is_active=True)
        if not opts["include_superusers"]:
            user_qs = user_qs.exclude(is_superuser=True)
        users = list(user_qs)

        if not users:
            raise CommandError("No candidate users found (check --include-superusers).")

        self.stdout.write(
            f"Found {len(resources)} resources and {len(users)} candidate users. "
            f"Levels pool: {levels}"
        )

        rows = []
        touched_resources = 0

        for resource in resources:
            # work on the real subtype instance so set_permissions() applies
            # correctly (handles Dataset/Document/Map-specific behaviour)
            resource = resource.get_self_resource()

            n_users = random.randint(opts["min_users"], min(opts["max_users"], len(users)))
            picked_users = random.sample(users, n_users)

            user_perm_spec = {}

            # keep the owner safe at "manage" level
            if resource.owner_id:
                owner = resource.owner
                user_perm_spec[owner.username] = LEVELS["manage"]

            for user in picked_users:
                if resource.owner_id and user.id == resource.owner_id:
                    continue  # already set above
                level = random.choice(levels)
                user_perm_spec[user.username] = LEVELS[level]
                rows.append((resource.id, resource.title, user.username, level))

            perm_spec = {"users": user_perm_spec, "groups": {}}

            if opts["randomize_anonymous"]:
                anon_level = random.choice(["view", "none"])
                if anon_level == "view":
                    user_perm_spec["AnonymousUser"] = LEVELS["view"]
                    rows.append((resource.id, resource.title, "AnonymousUser", "view"))
                # "none" -> simply don't add AnonymousUser to the spec

            if not opts["dry_run"]:
                with transaction.atomic():
                    resource.set_permissions(perm_spec)

            touched_resources += 1
            if touched_resources % 50 == 0:
                self.stdout.write(f"...processed {touched_resources}/{len(resources)} resources")

        if rows:
            with open(opts["csv_out"], "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["resource_id", "resource_title", "username", "level"])
                writer.writerows(rows)
            self.stdout.write(self.style.SUCCESS(
                f"Logged {len(rows)} permission assignments to {opts['csv_out']}"
            ))

        mode = "DRY RUN — no changes were saved" if opts["dry_run"] else "changes applied"
        self.stdout.write(self.style.SUCCESS(
            f"Done ({mode}). Resources touched: {touched_resources}."
        ))
