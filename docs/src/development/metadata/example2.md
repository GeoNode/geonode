# Example: Adding an handler

## Create the handler

```python
from geonode.metadata.handlers.abstract import MetadataHandler

class MySchemaHandler(MetadataHandler):
   pass
```

Register your handler so that the metadata manager is aware of it:

```python
from geonode.metadata.manager import metadata_manager

metadata_manager.add_handler("myhandler", MySchemaHandler)
```

## Create skeleton schema

In order to define multiple fields, it may be useful to create a skeleton schema and add the fields one by one.

This is a sample skeleton file `myproject.json`:

```json
{
  "p1_short_name": {
    "type": ["string", "null"],
    "minLength": 1,
    "maxLength": 255,
    "geonode:after": "title",
    "geonode:handler": "sparse"
  },

  "edition": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "label": {"type": "string"}
      },
    "geonode:handler": "myhandler"
    "geonode:thesaurus": "p1_edition_codelist"
  }
}
```

`p1_short_name`:
This is a brand new field, handled by the `SparseHandler`, so we do not want to handle it in `YourSchemaHandler`.
It will need to be registered as a SparseField.

`edition`:
This field is declared in GeoNode as a field handled by the `BaseHandler`. We are telling the manager that we want to handle it via `YourSchemaHandler`.
Also, we are defining it to be a codelist populated via the `p1_edition_codelist` thesaurus, which must be created.
Since we are declaring a new handler for this field, we'll need the logic to handle it.

## Registering sparse fields

You may want to register your stuff when initializing your app:

```python
def load_schema_file():
    with open(os.path.join(os.path.dirname(__file__), "schemas", "myproject.json")) as f:
        schema_file = json.load(f)

    return schema_file


def init():

    # register sparse fields:
    for property_name, subschema in load_schema_file().items():
        if subschema.get("geonode:handler", None) == "sparse":
            sparse_field_registry.register(property_name, subschema)

    metadata_manager.add_handler("myhandler", YourSchemaHandler)
```

## Generate schema

Then you need to implement the handler method that initializes its part of schema, `update_schema`:

```python
def update_schema(self, jsonschema, context, lang=None):

    schema_file = load_schema_file()

    # building the full schema using the external file
    for property_name, subschema in schema_file.items():

        # tries to set up "title" and "description"
        self._localize_subschema_labels(context, subschema, lang, property_name)

        if "geonode:handler" not in subschema:
            # set the default handler if not specified
            subschema.update({"geonode:handler": "myhandler"})
        else:
            # skip fields that have already been added to the sparsefield register
            if subschema.get("geonode:handler", None) == "sparse":
                continue

        # add this field's subschema to the full jsonschema
        self._add_subschema(jsonschema, property_name, subschema)
```

Now, since we took control of the `edition` field, we need to implement the methods that provide:

- the model-to-jsonschema transformation, `get_jsonschema_instance`
- the jsonschema-to-model transformation, `update_resource`

## Handle content

We need to decide what will be stored in the `edition` field.

The fields bound to thesauri are dicts with keys `id` and `label`, as also documented in the schema defined above.

We want to save into the `edition` field, which is defined in `ResourceBase` as a text field, some readable information. Let's use the default label from the `ThesaurusKeyword`.
In this thesaurus, **do not** define any localized labels, in order to be sure to get the default label as label.

When the jsonschema instance is returned, we have to provide the pair `(id, label)` anyway. We may retrieve the `KeywordLabel` by filtering by the default label, assuming that there are no duplicates. There may be other caveats, but just assume it is ok for the example.

### model-to-jsonschema

Let's search for the `ThesaurusKeyword` with the given default label, and create the return object:

```python
def get_jsonschema_instance(
    self, resource: ResourceBase, field_name: str, context: dict, errors: dict, lang: str = None
):
    match field_name:
        case "edition":
            if resource.edition:
                if tl := ThesaurusLabel.objects.filter(alt_label=resource.edition).first():
                    return {"id": tl.pk, "label": resource.edition}
            return {}
        case _:
            raise Exception(f"Unhandled field {field_name}")
```

### jsonschema-to-model

The jsonschema instance, if existing, is still a dict with keys `id` and `label`; we only return the label:

```python
def update_resource(
    self, resource, field_name, json_instance, context, errors, **kwargs
):
    field_value = json_instance.get(field_name, {})
    match field_name:
        case "edition":
            resource.edition = field_value.get("label", None)
        case _:
            raise Exception(f"Unhandled field {field_name}")
```
