# Source providers and data items

The `geonode.sources` app lets administrators connect GeoNode to external data sources and pick the items it should know about. It is the first layer of the catalog remodelling: it describes **what data exists**, independently of how the catalog will describe it or how it will be published.

!!! note
    A data item is **not** a `ResourceBase`. The app does not create resources nor publish anything: catalog records and publication will point at data items later on.

## Concepts

**Source provider**: code that knows how to read one kind of source (e.g. PostgreSQL). Providers are code, installed through the `SOURCE_PROVIDERS` setting and known only by the provider registry: nothing about them is stored in the database. Data items reference their provider by key (`source_provider`), set once at creation. A data item whose provider is not installed anymore stays in the database but cannot be read, and reports no capabilities.

**Connection**: the parameters needed to reach one source. A connection is an `AuthConfig` (the existing GeoNode credential store) whose `type` is the provider key, and whose encrypted payload holds the connection parameters. No secret is ever stored elsewhere.

**Data item**: a uniform handle on one thing a provider can read, e.g. one table. It stores the key of its provider, a provider-owned `uri` without secrets, relative to its connection (`auth_config`). The capabilities are not stored: they come from the provider. It also caches what the discovery found (`title`, `details`, `last_seen`), so listing the items never reaches the source.

**Discovery**: it runs when a connection is created through the API or the pages, and again whenever an administrator asks for it. A connection whose source cannot be read is not saved. Each discovery browses the source once and stores every entry as a data item: new entries are created, known ones are refreshed. Entries gone upstream are not deleted, since the catalog may still point at them: they are flagged `is_available=False` and become available again if they come back. Data items are never created one by one. A discovery that finds nothing while the connection still has available items is refused and changes nothing: it is more likely a wrong parameter, e.g. a mistyped schema, than every table dropped at once.

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

Connection parameters, validated by `PostgresConnectionForm`:

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
- Discovery goes through the OGR PostgreSQL driver, inside the request; testing a connection only performs the handshake.
- Access rights are enforced by PostgreSQL itself when the data is read.
- The item uris do not carry the host, port and database: every parameter of a connection can be edited, and its items follow it. After a change the next discovery matches the tables by schema and name, and flags the ones not found as not available.
- Leaving a value blank when editing a connection keeps the stored one, so the password does not have to be sent again.

## The WMS provider

| | |
| --- | --- |
| Key / `AuthConfig` type | `wms` |
| Declared capabilities | `READ` |
| Data item | one per named leaf layer of the GetCapabilities document: group layers only collect other layers |
| Data item uri | `wms:?layer=<name>`, relative to the connection |
| Data item details | `name`, `abstract`, `keywords`, `bbox` (west, south, east, north in EPSG:4326, or `null` when not advertised) |

Connection parameters, validated by `WmsConnectionForm`:

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
- Discovery runs inside the request, with a 30 seconds timeout.

## Administration

Only staff users can manage sources. Other logged in users get a `403`.

### Pages

The pages are a temporary, thin client of the REST API below: they render an empty shell and every read or change goes through `/api/v2/`, so anything they do is available to other integrations as well.

| Page | Purpose |
| --- | --- |
| `/sources/` | list of the connections, with a button to create a connection for each installed provider |
| `/sources/new/<provider>/` | connection form of a provider, built from its `connection_fields`; saving it runs the first discovery |
| `/sources/<id>/` | connection detail: the data items of the connection, with *Discover*, *Test connection* and *Delete* |

Connections can also be edited in the Django admin, under *Authentication Configurations*: the same validation applies there, but a connection created there gets its data items only when a discovery is run. Removing a data item through the API only removes the GeoNode row, the upstream table is never touched; the next discovery adds it back if the table still exists. Deleting a connection also removes all its data items, again without touching the upstream tables. A connection also used to authenticate resources or URL patterns cannot be deleted.

### REST API

All endpoints are under `/api/v2/` and require a staff user.

| Endpoint | Methods | Description |
| --- | --- | --- |
| `source-providers/` | `GET` | installed providers, their declared capabilities and the connection fields to render |
| `source-connections/` | `GET`, `POST` | connections, with the count of their available data items (`data_items_count`); `payload` is write only. `POST` also runs the first discovery and returns its result as `discovery`; `502` when the source cannot be read, and nothing is saved |
| `source-connections/<id>/` | `GET`, `PATCH`, `DELETE` | `DELETE` also removes the data items of the connection; `400` while the connection authenticates resources or URL patterns |
| `source-connections/<id>/test/` | `POST` | `{"success": true, "message": ""}` |
| `source-connections/<id>/discover/` | `POST` | stores the entries of the connection as data items: `{"found": 3, "created": 1, "missing": 1}`, where `missing` counts the items flagged not available by this run. `400` when it finds nothing while the connection has available items |
| `data-items/` | `GET` | data items, `?connection=<id>` keeps the ones of a connection |
| `data-items/<id>/` | `GET`, `DELETE` | |

Example:

```bash
curl -u admin:admin -H "Content-Type: application/json" -X POST \
  -d '{"type": "postgresql", "payload": {"host": "db", "database": "gis", "username": "reader", "password": "secret"}}' \
  http://localhost:8000/api/v2/source-connections/

curl -u admin:admin -X POST http://localhost:8000/api/v2/source-connections/1/discover/

curl -u admin:admin "http://localhost:8000/api/v2/data-items/?connection=1"
```

## Adding a provider

A provider lives in its own package under `geonode/sources/<key>/`:

- `auth.py`: a `geonode.sources.auth.FormAuthHandler` subclass whose `handled_type` is the provider key. It validates the payload with the connection form of the provider: blank values keep the stored ones, unknown keys are refused.
- `forms.py`: the connection form. It validates the payload and generates the fields the UI renders.
- `provider.py`: a `BaseSourceProvider` subclass defining `key`, `label`, `declared_capabilities`, `connection_form`, and implementing `test_connection` and `browse`. When the source cannot be read, `browse` raises a `RuntimeError`, e.g. `geonode.sources.base.SourceProviderError`: the API logs it and answers with a generic `502`.

Then register both classes in the settings:

```python
AUTH_HANDLERS += ["myapp.sources.mysource.auth.MySourceAuthHandler"]
SOURCE_PROVIDERS += ["myapp.sources.mysource.provider.MySourceProvider"]
```

GeoNode refuses to start if a provider has no connection form or no auth handler for its key.
