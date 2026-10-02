# Tracking the metadata changes

When `METADATA_TRACK_CHANGES` is enabled, every metadata save is compared with the state preceding
it, and what changed is recorded along with the user who requested it.

The comparison means reading the metadata of the resource once more, which is why the tracking is
opt-in. While disabled, nothing of what follows takes place.

## Declaring a change

The code about to change some metadata declares the operation and who requested it:

```python
from geonode.metadata.tracking.operation import metadata_tracker

with metadata_tracker(user):
    resource_manager.update(...)
```

Whatever happens inside the block, however many saves it takes, is one change performed by that
user. Nested blocks join the outer one, so a procedure calling another one does not end up exposing
its internal sequence as several changes.

The user is not optional: recording *what* changed without *who* changed it would defeat the
purpose. A block raising an exception records nothing, since a half applied change would be
misleading rather than informative.

## Changes nobody declared

A metadata save performed outside of any such block is still recorded, one change per save, under
the user named by `METADATA_TRACK_DEFAULTUSER`. Those records are marked as not attributed: the
change did happen, but the user it carries is not the one who requested it.

A warning naming the calling code is logged the first time each of such callers is met, so that the
places still to be declared can be found without reading through the whole stack.

## What a change looks like

Only what changed is reported:

```json
{
    "title": {"from": "Old title", "to": "New title"},
    "category": {"from": {"id": "biota", "label": "Biota"}, "to": null},
    "tkeywords": {
        "gemet-inspire-themes": {"added": [{"id": "http://...", "label": "Soil"}]}
    }
}
```

- a missing `from` means the field was not in the instance at all, which is not the same as being
  there with a null value;
- entries carrying both an `id` and a `label` are compared by id alone: the labels are localized,
  and reading the metadata in another language is not a change of metadata;
- lists are reported as added and removed entries; reordering one is not a change;
- an object such as `tkeywords` or `contacts` reports the entries that changed, not the whole of it.

## How it is put together

`TrackerHandler` is a metadata handler of its own, handling no field: it only takes the state
preceding the change, when the manager loads the deserialization context, and hands the comparison
over once the operation is over. It is declared in `FINAL_METADATA_HANDLERS` since what it reads has
to be the state every other handler has left behind.

The comparison itself is `geonode.metadata.tracking.delta.compute_delta()`, which is a plain function over
two schema instances.

Where the recorded change is finally stored is `geonode.metadata.tracking.operation.store_change()`.
