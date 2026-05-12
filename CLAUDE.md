# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What GeoNode is

GeoNode is a Django-based geospatial CMS. The repo root is a full Django *project* (settings, URL conf, wsgi, Celery app) that is also distributed as an installable package. End-user customization is expected to happen in a downstream project built from https://github.com/GeoNode/geonode-project — core files in this repo should not be modified for project-specific needs. The stack relies on PostgreSQL/PostGIS, Redis/Celery, and an OGC backend (GeoServer by default, configured via `OGC_SERVER["default"]["BACKEND"]`).

## Common commands

### Running inside Docker (typical dev flow)

- `python create-envfile.py [--env_type dev|test|prod] [--hostname ...] ...` — generates `.env`
- `docker compose build && docker compose up -d` — start full stack (django, celery, geoserver, db, rabbit/redis, nginx)
- `make sync` — run migrations + load `sample_admin`, `default_oauth_apps_docker`, `initial_data` fixtures
- `make reset` / `make hardreset` — down+up+sync, optionally rebuild from scratch
- `make logs` — follow container logs
- `make smoketest` / `make unittest` / `make test` — in-container test suites (see `Makefile`)

### Running locally (no docker)

- Env is loaded from `.env_dev` by wrapper scripts. `./manage_dev.sh <args>` runs `python manage.py <args>` with that env sourced; `./manage.sh` is the in-container equivalent (`/usr/src/venv`).
- `./celery_dev.sh` — local Celery worker with `.env_dev`; `./celery.sh` / `./celery-cmd` are the in-container versions.
- `ASYNC_SIGNALS` in the env controls whether post-save side effects fire synchronously or via Celery. Default is `False` in `.env_dev`.

### Tests

- `pytest` is configured (`pytest.ini` sets `DJANGO_SETTINGS_MODULE=geonode.settings`) for individual modules and BDD support.
- CI and `tests/test.sh` use Django's test runner via `manage.py test` with `coverage run`, loading `.env_test` and running `paver setup_data` first (seeds sample layers from the `gisdata` package). `tests/test_dev.sh` does the same but against `.env_dev` and skips `setup_data`.
- Run one test: `./manage_dev.sh test geonode.base.tests.test_models.SomeTest.test_x --keepdb -v 3`. Use `--keepdb` — the test DB is expensive to rebuild.
- `.github/workflows/tests.yml` partitions the suite into `smoke`, `main`, `security`, `gis_backend`, `rest_apis`, `csw`, `upload`. The partitioning is driven by substring filters on `settings.GEONODE_APPS` (see workflow for exact filters), so where an app lives in the app groups (below) affects which CI lane runs its tests.

### Lint/format

- `./flake8.sh` runs `flake8 geonode` (enforced by `.github/workflows/flake8.yml`).
- `black` is configured in `pyproject.toml` with `line-length = 120` and excludes `migrations/`, `settings.py`, `management/`, `scripts/`, `docs/`, `static/`, `node_modules/`.

## High-level architecture

### Settings and app groups

`geonode/settings.py` is ~2200 lines and is the single source of truth — no split settings layout. It reads heavily from env vars (`os.getenv` + `ast.literal_eval`), so feature flags live in env files (`.env_dev`, `.env_test`, `.env`), not Python. When a feature is not working in local dev, first check its env flag.

It defines three groups that are concatenated into `GEONODE_APPS` and appended to `INSTALLED_APPS`:

- **`GEONODE_CORE_APPS`** — resource model + metadata: `api`, `base`, `br`, `layers`, `maps`, `geoapps`, `documents`, `security`, `catalogue` (+ `metadataxsl`), `harvesting`, `metadata`.
- **`GEONODE_INTERNAL_APPS`** — supporting services: `people`, `client`, `themes`, `proxy`, `social`, `groups`, `services`, `management_commands_http`, `resource` (+ `processing`), `storage`, `geoserver` (+ `processing`), `upload`, `tasks`, `favorite`. **`geonode.geoserver` is deliberately listed last** so its signal handlers run after the rest.
- **`GEONODE_CONTRIB_APPS`** — opt-in add-ons. `geonode.indexing`, `geonode.facets`, `geonode.assets` are appended to `GEONODE_APPS` conditionally later in `settings.py`.

Decide which group a new feature belongs to — the split controls CI test partitioning.

### URL wiring

`geonode/urls.py` is the master URL conf. It mounts each app's `urls.py` (e.g. `^base/`, `^datasets/`, `^maps/`, `^documents/`, `^apps/` for geoapps, `^catalogue/`, `^groups/`, `^harvesters/`, `^services/`, `^people/`, `^upload/`, `^security/`, `^social/`, `^announcements/`, `^invitations/`). The REST v2 router is mounted at `^api/v2/` and aggregates sub-routers from multiple apps. GeoServer-dependent URLs (`^upload/`, `^capabilities/...`, `^gs/`) are gated by `check_ogc_backend(geoserver.BACKEND_PACKAGE)`.

## Map of the `geonode/` subfolder

This section focuses on the `geonode/` Python package — the actual Django application. Each entry is an installed app unless noted.

### Resource model and core catalog

- **`geonode/base/`** — the heart of the catalog. Defines **`ResourceBase`**, the polymorphic (django-polymorphic) superclass for all catalogable content, plus shared taxonomy models: `HierarchicalKeyword`, `ThesaurusKeyword`, `TopicCategory`, `Region`, `License`, `Link`, `ExtraMetadata`, `Favorite`, `LinkedResource`, `ContactRole`. Also hosts the v2 DRF API template — see `base/api/{views,serializers,filters,permissions,pagination,exceptions,mixins,fields}.py`. The viewset pattern here (dynamic-rest, `ApiPresetsInitializer`, `GeoNodeApiPagination` with a `resources` response key, `geonode_exception_handler` normalizing errors to `{success, errors, code}`) is the template other apps follow. Detailed walk-through in `memory/base_api_overview.md`.
- **`geonode/layers/`** — concrete `Dataset` + `Attribute` models (vector/raster/time-enabled layers), ingestion-metadata parser (`metadata.py`), download handler, and layer-specific v2 endpoints under `layers/api/`.
- **`geonode/maps/`** — `Map` + `MapLayer` models and v2 API. Maps are compositions of `Dataset`s / remote WMS layers, rendered by MapStore.
- **`geonode/documents/`** — `Document` model (non-geospatial uploads: PDFs, images, docs), EXIF extraction (`documents/exif/`), thumbnail tasks.
- **`geonode/geoapps/`** — `GeoApp` model, a generic container for custom client-defined applications backed by arbitrary `blob` JSON. Used by MapStore "GeoStory" and "Dashboard" types.

All four concrete resource models inherit `ResourceBase`. Because of polymorphism, a query on `ResourceBase` followed by `get_real_instance()` will trigger follow-up SELECTs per row unless explicitly avoided — a known source of N+1 patterns in the REST API.

### Resource lifecycle

- **`geonode/resource/`** — owns the **`ResourceManager`** (`resource/manager.py`), the canonical entry point for create/copy/update/delete/publish/permission-set operations. Prefer going through this manager rather than calling `ResourceBase.objects...save()` directly — it handles signals, thumbnails, linked resources, asset mapping, and permission inheritance. Also defines `ExecutionRequest` (the tracked-async-job record used by upload/copy/update endpoints) and the `processing/` sub-app.
- **`geonode/upload/`** — ingestion pipeline. The `ImportOrchestrator` (`upload/orchestrator.py`) picks a handler from `upload/handlers/` based on the file type (`csv`, `geojson`, `geotiff`, `gpkg`, `kml`, `shapefile`, `xlsx`, `empty_dataset`, ...). Each handler subclasses `BaseHandler` and registers itself. Work runs as a chain of Celery tasks on the `geonode.upload.*` queues. `upload/celery_app.py` is a *separate* Celery app (`importer_app`) from the main `geonode` Celery app, dedicated to the upload pipeline.
- **`geonode/assets/`** — pluggable storage for resource payload files. `AssetHandlerInterface` is the plug-in seam; `local.py` is the default on-disk implementation. `Asset` records link a resource to its underlying files independently of the resource model.
- **`geonode/storage/`** — abstraction over the backing file store. `StorageManager` dispatches to the configured Django storage (local / S3 via `boto3` / Dropbox / GCS). Use `storage_manager` rather than Django `default_storage` to keep upload paths consistent.
- **`geonode/thumbs/`** — thumbnail generation for datasets/maps/documents (WMS GetMap composition, background tiling algorithms, fallbacks). Invoked from resource tasks.

### Metadata

- **`geonode/metadata/`** — the v2 metadata framework. `MetadataManager` (`metadata/manager.py`) orchestrates a chain of `MetadataHandler`s (`metadata/handlers/`: `contact`, `doi`, `hkeyword`, `thesaurus`, `region`, `linkedresource`, `multilang`, `sparse`, ...) that each contribute a slice of the JSON Schema and its read/update behavior. `metadata/schemas/` holds the base JSON Schema (`base.json`). `metadata/multilang/` adds per-language fields. New metadata fields are added by implementing a handler and registering it.
- **`geonode/catalogue/`** — CSW interface (via `pycsw`). `catalogue/backends/` holds the pycsw backend plumbing; `catalogue/metadataxsl/` is a separate app that renders resource metadata XML via XSL transforms.
- **`geonode/harvesting/`** — background harvesters pulling metadata from remote catalogs into local `ResourceBase` records. `harvesting/harvesters/` contains the per-source drivers (`arcgis`, `geonodeharvester`, `wms`), each subclassing the base harvester. Tasks are on the `harvesting` queue. The main Celery app auto-discovers these tasks specifically: `app.autodiscover_tasks(packages=["geonode.harvesting.harvesters"])`.
- **`geonode/indexing/`** — Postgres `tsvector` search index over metadata. `TSVectorIndexManager` builds and refreshes `ResourceIndex` rows based on `settings.METADATA_INDEXES` and `settings.MULTILANG_FIELDS`. Consumed by the `ResourceIndexFilter` in the base API filter chain.
- **`geonode/facets/`** — facet providers for search UIs. Each provider in `facets/providers/` exposes counts (category, keyword, region, owner, resource type, thesaurus, ...) via `^api/v2/facets/`.

### Security and identity

- **`geonode/security/`** — permissions + permission workflow. Home of **`permissions_registry`** (`security/registry.py`), the single access point for resource visibility and per-object perms:
  - `permissions_registry.get_visible_resources(qs, user, ...)` — filter a queryset to what a user can see. Used by `ResourceBasePermissionsFilter`, the most expensive filter in the v2 API.
  - `permissions_registry.get_perms(instance, user)` — per-object permission list. Cached under `resource_perms:{pk}:{user_identifier}`.
  - `PermissionsHandler` subclasses (`security/handlers.py`) plug into `REGISTRY` to post-process permission lists and enforce moderation/publishing workflows. Relevant settings: `ADMIN_MODERATE_UPLOADS`, `RESOURCE_PUBLISHING`, `GROUP_PRIVATE_RESOURCES`.
  - `AdvancedSecurityWorkflowManager` (`security/utils.py`) applies those flags when a resource is created/updated.
  Backing store is django-guardian (`UserObjectPermission`, `GroupObjectPermission`). When listing resources, always route through `get_visible_resources()` / `get_resources_with_perms()` — don't reimplement Guardian lookups.
- **`geonode/people/`** — custom user model (`Profile` extending `AbstractUser`), allauth adapters, social-provider plug-in (`people/socialaccount/providers/geonode_openid_connect/`), and v2 users API (`people/api/`). Signup/login templates live here.
- **`geonode/groups/`** — `GroupProfile` and `GroupCategory` (extensions of Django groups with GeoNode-specific metadata and membership). Group-based visibility is enforced by security handlers when `GROUP_PRIVATE_RESOURCES` is on.
- **`geonode/invitations/`** (only `urls.py`) — thin wrapper over `django-invitations`.
- **`geonode/social/`** — activity stream integration (django-activity-stream): signals that post actions to the feed.

### OGC backend integration

- **`geonode/geoserver/`** — the default and only actively maintained backend. Exposes:
  - `BACKEND_PACKAGE`, `USE_GEOSERVER`, and `check_ogc_backend()` (in `geonode/utils.py`) gate URL includes and signal wiring. When touching layer/map code, grep for `check_ogc_backend(` / `USE_GEOSERVER` to find backend-gated branches.
  - `geoserver/manager.py` — `GeoServerResourceManager`, plugged into `ResourceManager` so resource operations fan out to GeoServer REST calls (catalog create/delete, styles, metadata sync).
  - `geoserver/geofence.py` — pushes GeoNode permissions to GeoServer's GeoFence ACL.
  - `geoserver/security.py`, `geoserver/signals.py`, `geoserver/ows.py` — glue layers for auth proxying and OGC capability publishing.
  - `geoserver/createlayer/` — on-the-fly empty-dataset creation in GeoServer.
- **`geonode/services/`** — remote OGC services (WMS/WFS/ArcGIS/WMTS). `services/serviceprocessors/` holds per-protocol drivers that register remote layers as `Dataset` records.
- **`geonode/proxy/`** — authenticated proxy for CORS-restricted OGC calls from the browser and download endpoints (handled by `django-downloadview`).
- **`geonode/client/`** — MapStore integration. Pairs with `django_geonode_mapstore_client` (installed from GitHub master in `pyproject.toml`).

### Platform plumbing

- **`geonode/api/`** — the *legacy* Tastypie v1 API (`^api/`, `api.urls.api`) **and** the central v2 DRF router (`api.urls.router`) that other apps register their viewsets on. Prefer not extending v1; new endpoints should be DRF viewsets registered to `router`.
- **`geonode/management_commands_http/`** — HTTP wrapper over a whitelisted set of Django management commands (`^api/v2/`), used by the admin UI.
- **`geonode/tasks/`** — Celery task wrappers (exposed in `INSTALLED_APPS` to provide shared periodic jobs and queues).
- **`geonode/br/`** — backup & restore management commands.
- **`geonode/favorite/`**, **`geonode/themes/`** — small user-facing apps: favourites list, site theming.
- **`geonode/notifications_helper.py`** + `pinax-notifications` — email/in-app notifications layer.
- **`geonode/middleware.py`**, **`geonode/middleware.py` (per app)** — request-scoped handlers (allowed hosts, read-only when loading, maintenance, session-expired redirect). `geonode/base/middleware.py` contains the maintenance-mode gate.
- **`geonode/celery_app.py`** — the main Celery app (`geonode`). Auto-discovers tasks from all installed apps and explicitly from `geonode.harvesting.harvesters`. Queue list is defined in `settings.py` (`default`, `geonode`, `update`, `upload`, `cleanup`, `email`, `security`, `management_commands_http`, `harvesting`, plus a family of `geonode.upload.*` queues and GeoServer broadcast queues). Pick an existing queue when adding a task.
- **`geonode/context_processors.py`, `templates/`, `static/`, `locale/`** — server-side rendering bits for pages not served by MapStore.

## REST API surface

Two parallel API stacks coexist:

- **`/api/` (v1)** — legacy Tastypie, in `geonode.api.resourcebase_api` et al. Still wired into the URL conf for backwards compatibility. Prefer **not** extending.
- **`/api/v2/` (current)** — DRF + `dynamic_rest`. Routers are registered in individual apps (`geonode.base.api`, `geonode.layers.api`, `geonode.maps.api`, `geonode.documents.api`, `geonode.geoapps.api`, `geonode.people.api`, `geonode.facets.urls`, `geonode.assets.urls`, `geonode.metadata.api.urls`, `geonode.upload.api`). The central router is `geonode.api.urls.router`; mount your viewsets there.

Follow `geonode.base.api` as the model:
- Filter backends in `filters.py`; paginate with `pagination.GeoNodeApiPagination` (body uses `resources`, not `results`).
- Permissions in `permissions.py`; surface errors via `exceptions.geonode_exception_handler` → `{success, errors, code}`.
- `ApiPresetsInitializer` expands `api_preset` query params into full filter sets.
- Dynamic-rest field deferral: `?include[]=metadata`, `?include[]=data`, `?include[]=executions`, `?include[]=linked_resources` trigger extra queries.

## Async / background work

- The main `geonode` Celery app lives at `geonode/celery_app.py`. A separate `importer_app` lives at `geonode/upload/celery_app.py`, dedicated to the upload pipeline — their queues are disjoint.
- `ASYNC_SIGNALS=False` (default in `.env_dev` and tests) makes post-save side effects — thumbnail regeneration, GeoServer catalog sync, permission propagation, etc. — run synchronously in-request. Turn it on to exercise the real async path.
- When a new task depends on an existing service (GeoServer, harvesting, upload), route it to that service's queue rather than spawning a new one.

## Memory/context references

- `memory/base_api_overview.md` — detailed code-path analysis of `geonode/base/api/` including serializer field-level DB impact and a numbered bottleneck map. It is a point-in-time snapshot; verify against current code before quoting line numbers.
