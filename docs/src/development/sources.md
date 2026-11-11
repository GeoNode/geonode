# Source providers and data items

The `geonode.sources` app lets administrators connect GeoNode to external data sources and pick the items it should know about. It is the first layer of the catalog remodelling: it describes **what data exists**, independently of how the catalog will describe it or how it will be published.

!!! note
    A data item is **not** a `ResourceBase`. The app does not create resources nor publish anything: catalog records and publication will point at data items later on.

## Concepts

**Source provider**: code that knows how to read one kind of source (e.g. PostgreSQL). Providers are code, installed through the `SOURCE_PROVIDERS` setting and known only by the provider registry: nothing about them is stored in the database. Data items reference their provider by key (`source_provider`), set once at creation. A data item whose provider is not installed anymore stays in the database but cannot be read, and reports no capabilities.

**Connection**: the parameters needed to reach one source. A connection is an `AuthConfig` (the existing GeoNode credential store) whose `type` is the provider key, and whose encrypted payload holds the connection parameters. No secret is ever stored elsewhere.

**Data item**: a uniform handle on one thing a provider can read, e.g. one table. It stores the key of its provider, a provider-owned `uri` without secrets, relative to its connection (`auth_config`). The capabilities are not stored: they come from the provider. It also keeps the `title` and `details` read from the source when it was adopted, so listing the items never reaches the source.

**Browsing**: a live call that lists what a connection exposes right now. Nothing is stored: each entry only tells whether it is already a data item (`adopted`).

**Adoption**: the moment of durable interest. An administrator picks some of the browsed entries and each one becomes a data item. The source is browsed again at that point, so `title` and `details` always come from the source and an entry the connection does not expose is refused, along with the whole request. Adopting an entry twice changes nothing. Creating a connection does not create any data item: it only checks that the source can be reached, and a connection that cannot be reached is not saved.

### Capabilities

Each provider declares what it can do with its items, and every data item of the provider has those capabilities:

| Capability | Meaning |
| --- | --- |
| `READ` | the content can be read (features, pixels or raw bytes) |
| `WRITE` | the content can be changed upstream |
| `SCHEMA` | the structure can be described (attributes, geometry type, srid) |
| `TRANSACTIONAL` | several writes can be committed or rolled back together |

A missing capability is a statement, not a gap: an item without `SCHEMA` has no attributes to read.

## The PostgreSQL provider

| | |
| --- | --- |
| Key / `AuthConfig` type | `postgresql` |
| Declared capabilities | `READ` |
| Data item | one per table or view of the connection schema |
| Data item uri | `postgresql:?schema=<schema>&table=<table>`, relative to the connection |

It works with or without the PostGIS extension: tables without geometry are listed with an empty geometry list.

Connection parameters, validated by `PostgresConnectionSerializer`:

| Parameter | Required | Default | Notes |
| --- | --- | --- | --- |
| `host` | yes | | |
| `port` | no | `5432` | |
| `database` | yes | | |
| `username` | yes | | |
| `password` | yes | | never returned by the API or shown in the pages |
| `sslmode` | no | `prefer` | any libpq ssl mode |
| `schema` | no | `public` | the schema browsed by the connection |

Notes:

- Every session is opened read-only, with a connect and a statement timeout.
- Browsing goes through the OGR PostgreSQL driver, inside the request; testing or creating a connection only performs the handshake.
- Access rights are enforced by PostgreSQL itself when the data is read.
- The item uris do not carry the host, port and database: every parameter of a connection can be edited, and its items follow it. Nothing checks the adopted items after a change: an item whose table is not in the new database or schema stays, and cannot be read.
- Leaving a value blank when editing a connection keeps the stored one, so the password does not have to be sent again.

## The WMS provider

| | |
| --- | --- |
| Key / `AuthConfig` type | `wms` |
| Declared capabilities | `READ` |
| Data item | one per named leaf layer of the GetCapabilities document: group layers only collect other layers |
| Data item uri | `wms:?layer=<name>`, relative to the connection |
| Data item details | `name`, `abstract`, `keywords`, `bbox` (west, south, east, north in EPSG:4326, or `null` when not advertised) |

Connection parameters, validated by `WmsConnectionSerializer`:

| Parameter | Required | Default | Notes |
| --- | --- | --- | --- |
| `url` | yes | | the service url; `service`, `request` and `version` are removed from it, vendor parameters such as `map=` are kept |
| `version` | no | `1.3.0` | `1.3.0` or `1.1.1` |
| `username` | no | | basic authentication, together with `password` |
| `password` | no | | never returned by the API or shown in the pages |

Notes:

- The capabilities are fetched through `geonode.utils.safe_request_url`: only `http` and `https`, no credentials in the url, and no private, loopback or link-local host, checked on every redirect too. A service on such a host, e.g. a local GeoServer in development, must be listed in `SAFE_URL_TRUSTED_HOSTS` as `host:port`.
- The document is parsed without resolving entities nor reaching the network, then read by owslib through `geonode.utils.WebMapService`.
- Credentials are sent as basic authentication: prefer an `https` url when they are set.
- Creating, testing, browsing and adopting each fetch the capabilities inside the request, with a 30 seconds timeout.

## Administration

Only staff users can manage sources. Other logged in users get a `403`.

### Pages

The pages are a temporary, thin client of the REST API below: they render an empty shell and every read or change goes through `/api/v3/`, so anything they do is available to other integrations as well.

| Page | Purpose |
| --- | --- |
| `/sources/` | list of the connections, with a button to create a connection for each installed provider |
| `/sources/new/<provider>/` | connection form of a provider, built from its `connection_fields`; saving it checks that the source can be reached |
| `/sources/<id>/` | connection detail: its parameters, a *Data items* tab, and a *Browse the source* tab listing what the source exposes, page by page, to select and adopt (adopted entries are marked); plus *Test connection* and *Delete* |

Connections can also be edited in the Django admin, under *Authentication Configurations*: the same validation applies there, but the source is not checked. Removing a data item through the API only removes the GeoNode row, the upstream table is never touched; it can be adopted again while the table exists. Deleting a connection also removes all its data items, again without touching the upstream tables. A connection also used to authenticate resources or URL patterns cannot be deleted.

### REST API

All endpoints are under `/api/v3/` and require a staff user. Their OpenAPI schema is served at `/api/v3/schema/`, with Swagger UI at `/api/v3/schema/swagger-ui/`.

The API follows the API v3 conventions: a single object is returned as is, lists are paginated as `{"count", "next", "previous", "results"}` with the `page` and `page_size` parameters (default 10, at most `REST_API_V3_MAX_PAGE_SIZE`), and `?fields=id,title` returns only the named fields (`data-items/` leaves `details` out unless asked). Errors are [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) Problem Details, served as `application/problem+json`: `{"type", "title", "status", "detail", "code"}`, plus `errors` keyed by field on a `400`. `source-connections/<id>/browse/` is paginated too, but it stays live: every page lists the source again.

| Endpoint | Methods | Description |
| --- | --- | --- |
| `source-providers/` | `GET` | installed providers, their declared capabilities and the connection fields to render |
| `source-connections/` | `GET`, `POST` | connections, with the count of their data items (`data_items_count`); `payload` is write only. `POST` checks that the source can be reached: `502` when it cannot, and nothing is saved |
| `source-connections/<id>/` | `GET`, `PATCH`, `DELETE` | `DELETE` also removes the data items of the connection; `409` while the connection authenticates resources or URL patterns |
| `source-connections/<id>/test/` | `POST` | `{"success": true, "message": ""}` |
| `source-connections/<id>/browse/` | `GET` | what the connection exposes right now, nothing is stored: a page of `{"uri", "title", "details", "adopted"}`. `502` when the source cannot be read |
| `source-connections/<id>/adopt/` | `POST` | `{"uris": [...]}`, 1 to 100 uris taken from `browse/`: stores them as data items and returns them with a `201`, the ones already adopted are returned unchanged. `400` when one of the uris is not exposed by the connection, and nothing is stored; `502` when the source cannot be read |
| `data-items/` | `GET` | data items, filtered with `?connection=<id>` and `?source_provider=<key>`; `400` for an unknown connection |
| `data-items/<id>/` | `GET`, `DELETE` | |

Example:

```bash
curl -u admin:admin -H "Content-Type: application/json" -X POST \
  -d '{"type": "postgresql", "payload": {"host": "db", "database": "gis", "username": "reader", "password": "secret"}}' \
  http://localhost:8000/api/v3/source-connections/

curl -u admin:admin http://localhost:8000/api/v3/source-connections/1/browse/

curl -u admin:admin -H "Content-Type: application/json" -X POST \
  -d '{"uris": ["postgresql:?schema=public&table=roads"]}' \
  http://localhost:8000/api/v3/source-connections/1/adopt/

curl -u admin:admin "http://localhost:8000/api/v3/data-items/?connection=1"
```

## Adding a provider

A provider lives in its own package under `geonode/sources/<key>/`:

- `auth.py`: a `geonode.sources.auth.SourceConnectionAuthHandler` subclass whose `handled_type` is the provider key. It validates the payload with the connection serializer of the provider: blank values keep the stored ones, unknown keys are refused.
- `serializers.py`: the connection serializer, a DRF `Serializer`. It validates the payload and generates the fields the UI renders: a password field is a `CharField` with `style={"input_type": "password"}`.
- `provider.py`: a `BaseSourceProvider` subclass defining `key`, `label`, `declared_capabilities`, `connection_serializer`, and implementing `test_connection` and `browse`. `browse` is called live, by browsing and by adoption. When the source cannot be read it raises a `RuntimeError`, e.g. `geonode.sources.base.SourceProviderError`: the API logs it and answers with a generic `502`.

Then register both classes in the settings:

```python
AUTH_HANDLERS += ["myapp.sources.mysource.auth.MySourceAuthHandler"]
SOURCE_PROVIDERS += ["myapp.sources.mysource.provider.MySourceProvider"]
```

GeoNode refuses to start if a provider has no connection serializer or no auth handler for its key.
