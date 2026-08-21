"""
Single Django management command that runs the full load-test pipeline:

    1) create N users
    2) create M random resources (documents/maps, best-effort datasets)
    3) randomly (re)assign permissions across resources

INSTALL
-------
Drop this file into any GeoNode app's management/commands package, e.g.:

    geonode/base/management/commands/run_full_load_test.py

(create the `management/` and `management/commands/` dirs with empty
__init__.py files if they don't already exist).

USAGE
-----
    python manage.py run_full_load_test \
        --num-users 1000 \
        --num-resources 1000 --resource-type document,map \
        --min-users 1 --max-users 5 \
        --csv-out-prefix load_test

    # preview only, nothing written to the DB:
    python manage.py run_full_load_test --num-users 20 --num-resources 20 --dry-run

Everything is printed to the console as it happens (stage banners, batch
progress every 100 items, and a final summary table) so you can follow the
run live or pipe it to a logfile with e.g. `... | tee load_test.log`.

KEY OPTIONS
-----------
Users (stage 1):
    --num-users        N     how many users to create (default 1000)
    --user-prefix      STR   username/email prefix (default "testuser")
    --user-domain      STR   email domain (default "example.com")
    --user-password    STR   fixed password for all new users (random per-user if omitted)
    --user-start       N     starting numeric suffix (default 1)
    --group            STR   existing group to add new users to (optional)

Resources (stage 2):
    --num-resources    N     how many resources to create (default 1000)
    --resource-type    CSV   subset of document,map,dataset (default "document,map")
    --resource-prefix  STR   title prefix (default "AutoResource")

Permissions (stage 3):
    --min-users        N     min users touched per resource (default 1)
    --max-users        N     max users touched per resource (default 5)
    --levels           CSV   subset of view,download,edit,manage (default all four)
    --randomize-anonymous   also randomly flip public/anonymous view access
    --permissions-scope     "created" = only resources this run just made (default)
                            "all"     = every ResourceBase in the instance

Shared:
    --include-superusers    allow superusers to be picked as owners / permission subjects
    --seed             N     random seed, for reproducible runs
    --csv-out-prefix   STR   base filename for the 3 CSV logs written
                             (<prefix>_users.csv, <prefix>_resources.csv, <prefix>_permissions.csv)
    --dry-run                compute everything, print it, but write nothing to the DB
"""

import csv
import random
import string
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from geonode.base.models import ResourceBase, TopicCategory
from geonode.documents.models import Document
from geonode.maps.models import Map

User = get_user_model()

RESOURCE_TYPES = ["document", "map", "dataset"]

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

WORD_POOL = [
    "river", "forest", "urban", "coastal", "seismic", "rainfall", "elevation",
    "landcover", "boundary", "soil", "wetland", "traffic", "population",
    "temperature", "vegetation", "flood", "geology", "cadastral", "network", "survey",
]


def random_words(n=3):
    return " ".join(random.choice(WORD_POOL) for _ in range(n))


def random_suffix(n=6):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def random_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choice(alphabet) for _ in range(length))


def model_field_names(model):
    """Field names actually present on this model in the running GeoNode version."""
    return {f.name for f in model._meta.get_fields()}


def find_file_field_name(model):
    """Find the first FileField (or subclass, e.g. ImageField) on a model, if any."""
    from django.db.models import FileField
    for f in model._meta.get_fields():
        if isinstance(f, FileField):
            return f.name
    return None


class Command(BaseCommand):
    help = "Full load-test pipeline: create users -> create random resources -> randomize permissions."

    def add_arguments(self, parser):
        # stage 1 - users
        parser.add_argument("--num-users", type=int, default=1000)
        parser.add_argument("--user-prefix", type=str, default="testuser")
        parser.add_argument("--user-domain", type=str, default="example.com")
        parser.add_argument("--user-password", type=str, default=None)
        parser.add_argument("--user-start", type=int, default=1)
        parser.add_argument("--group", type=str, default=None)

        # stage 2 - resources
        parser.add_argument("--num-resources", type=int, default=1000)
        parser.add_argument("--resource-type", type=str, default="document,map")
        parser.add_argument("--resource-prefix", type=str, default="AutoResource")

        # stage 3 - permissions
        parser.add_argument("--min-users", type=int, default=1)
        parser.add_argument("--max-users", type=int, default=5)
        parser.add_argument("--levels", type=str, default="view,download,edit,manage")
        parser.add_argument("--randomize-anonymous", action="store_true")
        parser.add_argument("--permissions-scope", choices=["created", "all"], default="created")

        # shared
        parser.add_argument("--include-superusers", action="store_true")
        parser.add_argument("--seed", type=int, default=None)
        parser.add_argument("--csv-out-prefix", type=str, default="load_test")
        parser.add_argument("--dry-run", action="store_true")

    # ---------- small logging helper (plain print, prefixed by stage) ----------
    def log(self, stage, msg, level="INFO"):
        style = {"INFO": self.style.NOTICE, "WARN": self.style.WARNING, "ERROR": self.style.ERROR}.get(level, str)
        self.stdout.write(style(f"[{stage:^11}] {msg}"))

    def handle(self, *args, **opts):
        if opts["seed"] is not None:
            random.seed(opts["seed"])

        types = [t.strip() for t in opts["resource_type"].split(",") if t.strip()]
        for t in types:
            if t not in RESOURCE_TYPES:
                raise CommandError(f"Unknown resource type '{t}'. Valid: {', '.join(RESOURCE_TYPES)}")

        levels = [lvl.strip() for lvl in opts["levels"].split(",") if lvl.strip()]
        for lvl in levels:
            if lvl not in LEVELS:
                raise CommandError(f"Unknown level '{lvl}'. Valid: {', '.join(LEVELS)}")

        if opts["min_users"] > opts["max_users"]:
            raise CommandError("--min-users cannot be greater than --max-users")

        dry_run = opts["dry_run"]

        self.log("SETUP", "=" * 60)
        self.log("SETUP", f"num_users={opts['num_users']} num_resources={opts['num_resources']} "
                           f"resource_type={types} min_users={opts['min_users']} max_users={opts['max_users']} "
                           f"levels={levels} scope={opts['permissions_scope']} dry_run={dry_run}")
        self.log("SETUP", "=" * 60)

        # ================= STAGE 1: USERS =================
        self.log("USERS", f"Creating {opts['num_users']} users "
                           f"(prefix={opts['user_prefix']!r}, domain={opts['user_domain']!r}) ...")

        group = None
        if opts["group"]:
            group = Group.objects.filter(name=opts["group"]).first()
            if not group:
                self.log("USERS", f"Group '{opts['group']}' not found — users created without a group.", "WARN")

        created_users, skipped_users, user_rows = [], [], []

        with transaction.atomic():
            for i in range(opts["user_start"], opts["user_start"] + opts["num_users"]):
                username = f"{opts['user_prefix']}{i}"
                email = f"{opts['user_prefix']}{i}@{opts['user_domain']}"

                if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
                    skipped_users.append(username)
                    continue

                password = opts["user_password"] or random_password()

                if not dry_run:
                    user = User.objects.create_user(username=username, email=email, password=password)
                    user.is_active = True
                    user.save(update_fields=["is_active"])
                    if group:
                        user.groups.add(group)

                created_users.append(username)
                user_rows.append((username, email, password))

                if len(created_users) % 100 == 0:
                    self.log("USERS", f"...{len(created_users)}/{opts['num_users']} users created")

            if dry_run:
                transaction.set_rollback(True)

        self.log("USERS", f"Done. Created: {len(created_users)}, Skipped (already existed): {len(skipped_users)}")

        # ================= build the user pool used for owners / permission subjects =================
        user_qs = User.objects.filter(is_active=True)
        if not opts["include_superusers"]:
            user_qs = user_qs.exclude(is_superuser=True)
        if dry_run:
            # in dry-run nothing new was persisted, so fall back to whatever already exists
            all_users = list(user_qs)
        else:
            all_users = list(user_qs.filter(username__in=created_users)) or list(user_qs)

        if not all_users:
            raise CommandError("No candidate users available for resource ownership / permissions "
                                "(check --include-superusers, or that user creation actually ran).")
        self.log("USERS", f"Owner/permission candidate pool size: {len(all_users)}")

        # ================= STAGE 2: RESOURCES =================
        self.log("RESOURCES", f"Creating {opts['num_resources']} resources of type(s) {types} ...")

        categories = list(TopicCategory.objects.all())
        existing_datasets = None

        # introspect the actual Document/Map fields available in this GeoNode version,
        # since these have changed across releases (e.g. Map viewer state fields,
        # Document's file field name)
        map_fields = model_field_names(Map)
        document_fields = model_field_names(Document)
        document_file_field = find_file_field_name(Document)
        warned_map_fields = False
        warned_doc_file = False

        if document_file_field is None:
            self.log("RESOURCES", "No FileField found on the Document model in this GeoNode version — "
                                   "documents will be created as metadata-only "
                                   "(using doc_url if available, otherwise no file at all).", "WARN")

        create_single_dataset = None
        if "dataset" in types:
            try:
                from geonode.base.populate_test_data import create_single_dataset as _csd
                create_single_dataset = _csd
            except ImportError:
                self.log("RESOURCES", "geonode.base.populate_test_data.create_single_dataset not importable "
                                       "in this GeoNode version — 'dataset' creation will be skipped.", "WARN")

        created_counts = {t: 0 for t in types}
        skipped_counts = {t: 0 for t in types}
        resource_rows = []
        created_resources = []  # actual resource objects, used for stage 3 scope="created"

        for i in range(1, opts["num_resources"] + 1):
            rtype = random.choice(types)
            owner = random.choice(all_users)
            title = f"{opts['resource_prefix']} {rtype} {random_words(2)} {i}"
            abstract = f"Auto-generated {rtype} for load testing: {random_words(6)}."
            category = random.choice(categories) if categories else None

            if dry_run:
                created_counts[rtype] += 1
                resource_rows.append((None, rtype, title, owner.username))
                continue

            resource = None
            try:
                with transaction.atomic():
                    if rtype == "document":
                        doc = Document(title=title, abstract=abstract, owner=owner, category=category)

                        if document_file_field:
                            content = f"Synthetic test document {uuid.uuid4()}\n{abstract}".encode()
                            getattr(doc, document_file_field).save(
                                f"{random_suffix()}.txt", ContentFile(content), save=False
                            )
                        elif "doc_url" in document_fields:
                            doc.doc_url = f"https://example.com/fake-doc-{random_suffix()}.txt"

                        doc.save()
                        resource = doc

                    elif rtype == "map":
                        desired_map_kwargs = dict(
                            title=title, abstract=abstract, owner=owner, category=category,
                            zoom=random.randint(1, 18),
                            center_x=round(random.uniform(-180, 180), 4),
                            center_y=round(random.uniform(-85, 85), 4),
                            projection="EPSG:3857",
                        )
                        map_kwargs = {k: v for k, v in desired_map_kwargs.items() if k in map_fields}
                        dropped = sorted(set(desired_map_kwargs) - set(map_kwargs))
                        if dropped and not warned_map_fields:
                            self.log("RESOURCES", f"Map model in this GeoNode version has no field(s) "
                                                   f"{dropped} — creating maps without viewer state "
                                                   f"(title/abstract/owner/category only).", "WARN")
                            warned_map_fields = True

                        m = Map(**map_kwargs)
                        m.save()
                        resource = m
                        if existing_datasets is None:
                            from geonode.layers.models import Dataset
                            existing_datasets = list(Dataset.objects.all()[:200])
                        if existing_datasets:
                            try:
                                from geonode.maps.models import MapLayer
                                ds = random.choice(existing_datasets)
                                MapLayer.objects.create(
                                    map=m,
                                    name=ds.alternate if hasattr(ds, "alternate") else ds.name,
                                    ows_url=getattr(ds, "ows_url", "") or "",
                                    stack_order=0,
                                    visibility=True,
                                )
                            except Exception:
                                pass

                    elif rtype == "dataset":
                        if not create_single_dataset:
                            skipped_counts[rtype] += 1
                            continue
                        ds = create_single_dataset(f"{opts['resource_prefix'].lower()}_{random_suffix()}")
                        ds.title = title
                        ds.abstract = abstract
                        ds.owner = owner
                        if category:
                            ds.category = category
                        ds.save()
                        resource = ds

            except Exception as exc:
                skipped_counts[rtype] += 1
                self.log("RESOURCES", f"Skipped a {rtype} ({title!r}): {exc}", "WARN")
                continue

            created_counts[rtype] += 1
            resource_rows.append((resource.id, rtype, title, owner.username))
            created_resources.append(resource)

            total_done = sum(created_counts.values())
            if total_done % 100 == 0:
                self.log("RESOURCES", f"...{total_done}/{opts['num_resources']} resources created")

        self.log("RESOURCES", f"Done. Created: {created_counts}. Skipped: {skipped_counts}")

        # ================= STAGE 3: PERMISSIONS =================
        if opts["permissions_scope"] == "all":
            target_resources = list(ResourceBase.objects.all())
            self.log("PERMISSIONS", f"Scope=all -> {len(target_resources)} resources in the whole instance")
        else:
            target_resources = created_resources
            self.log("PERMISSIONS", f"Scope=created -> {len(target_resources)} resources created in this run")

        if dry_run:
            self.log("PERMISSIONS", "Dry run: skipping actual permission assignment "
                                     "(nothing was persisted in stage 1/2 to attach permissions to).")
            perm_rows = []
        else:
            perm_rows = []
            touched = 0
            for resource in target_resources:
                resource = resource.get_self_resource()
                n_users = random.randint(opts["min_users"], min(opts["max_users"], len(all_users)))
                picked_users = random.sample(all_users, n_users)

                user_perm_spec = {}
                if resource.owner_id:
                    user_perm_spec[resource.owner.username] = LEVELS["manage"]

                for user in picked_users:
                    if resource.owner_id and user.id == resource.owner_id:
                        continue
                    level = random.choice(levels)
                    user_perm_spec[user.username] = LEVELS[level]
                    perm_rows.append((resource.id, resource.title, user.username, level))

                if opts["randomize_anonymous"] and random.choice([True, False]):
                    user_perm_spec["AnonymousUser"] = LEVELS["view"]
                    perm_rows.append((resource.id, resource.title, "AnonymousUser", "view"))

                resource.set_permissions({"users": user_perm_spec, "groups": {}})

                touched += 1
                if touched % 100 == 0:
                    self.log("PERMISSIONS", f"...{touched}/{len(target_resources)} resources given new permissions")

            self.log("PERMISSIONS", f"Done. Resources touched: {touched}. Assignments logged: {len(perm_rows)}")

        # ================= CSV logs =================
        prefix = opts["csv_out_prefix"]

        if user_rows:
            path = f"{prefix}_users.csv"
            with open(path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["username", "email", "password"])
                w.writerows(user_rows)
            self.log("SUMMARY", f"Wrote {len(user_rows)} user credentials to {path}")

        if resource_rows:
            path = f"{prefix}_resources.csv"
            with open(path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["resource_id", "resource_type", "title", "owner"])
                w.writerows(resource_rows)
            self.log("SUMMARY", f"Wrote {len(resource_rows)} created resources to {path}")

        if perm_rows:
            path = f"{prefix}_permissions.csv"
            with open(path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["resource_id", "resource_title", "username", "level"])
                w.writerows(perm_rows)
            self.log("SUMMARY", f"Wrote {len(perm_rows)} permission assignments to {path}")

        # ================= final summary =================
        mode = "DRY RUN — no changes were saved" if dry_run else "changes applied"
        self.log("SUMMARY", "=" * 60)
        self.log("SUMMARY", f"FINISHED ({mode})")
        self.log("SUMMARY", f"  users:       created={len(created_users)} skipped={len(skipped_users)}")
        self.log("SUMMARY", f"  resources:   created={created_counts} skipped={skipped_counts}")
        self.log("SUMMARY", f"  permissions: assignments={len(perm_rows)} "
                             f"(scope={opts['permissions_scope']})")
        self.log("SUMMARY", "=" * 60)
