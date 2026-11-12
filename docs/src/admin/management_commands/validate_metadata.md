# Validate Resource Metadata

The `validate_metadata` `Management Command` validates the metadata of GeoNode resources against the metadata `jsonschema`: for each resource, the schema instance is built and checked, and a report is produced listing which resources are invalid and why.

It can also validate metadata outside of GeoNode entirely, given a schema file and one or more instance files, which is useful to check a custom schema or a set of sample instances before deploying them.

First, let us take a look at the `--help` option of the `validate_metadata` management command in order to inspect all the command options and features.

Run:

```bash
DJANGO_SETTINGS_MODULE=geonode.settings python manage.py validate_metadata --help
```

This produces output similar to the following:

```bash
usage: manage.py validate_metadata [-h] [--id IDS [IDS ...]]
                                    [--resource-type RESOURCE_TYPES [RESOURCE_TYPES ...]]
                                    [--lang LANG] [--include-valid]
                                    [--no-error-details]
                                    [--max-errors MAX_ERRORS]
                                    [--check-formats] [--format {json,csv}]
                                    [--output OUTPUT] [--schema SCHEMA_FILE]
                                    [--instance INSTANCE_FILES [INSTANCE_FILES ...]]
                                    [--debug] [--version] [-v {0,1,2,3}]
                                    [--settings SETTINGS]
                                    [--pythonpath PYTHONPATH] [--traceback]
                                    [--no-color]

Validate the metadata of the GeoNode resources: the jsonschema instance of
each resource is built and validated against the metadata jsonschema. Empty
fields are only reported when mandatory, and only at top level: within a
nested object every unset field is reported. Exits with 1 if any resource is
invalid, 2 if the schema itself is, 3 if both

options:
  -h, --help            show this help message and exit
  --id IDS [IDS ...]    Only validate these resource ids (space and/or comma
                        separated)
  --resource-type RESOURCE_TYPES [RESOURCE_TYPES ...]
                        Only validate these resource types, e.g. dataset map
                        document (space and/or comma separated)
  --lang LANG           Language used to build the schema and the schema
                        instances (default: schema default)
  --include-valid       Also report the resources that validate successfully
                        (default: only the invalid ones)
  --no-error-details    Only report the number of errors, without the
                        details of each single error
  --max-errors MAX_ERRORS
                        Max number of errors reported per resource; 0
                        (default) means no limit. The error count is not
                        affected by this limit
  --check-formats       Also enforce the jsonschema "format" keyword (needs
                        the jsonschema format extra installed)
  --format {json,csv}   Output format (default: json)
  --output OUTPUT       Write the report to this file (default: stdout)
  --schema SCHEMA_FILE  Read the jsonschema from this file instead of
                        building it through the metadata manager
  --instance INSTANCE_FILES [INSTANCE_FILES ...]
                        Validate the jsonschema instances read from these
                        files, one instance per file, instead of the stored
                        resources. Not compatible with --id and
                        --resource-type
  --debug               Set log level to debug
  --version             show program's version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output,
                        2=verbose output, 3=very verbose output
  --settings SETTINGS   The Python path to a settings module, e.g.
                        "myproject.settings.main". If this isn't provided, the
                        DJANGO_SETTINGS_MODULE environment variable will be
                        used.
  --pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g.
                        "/home/djangoprojects/myproject".
  --traceback           Raise on CommandError exceptions
  --no-color            Don't colorize the command output.
```

## Report format

The report has two parts: a `summary` (free-text lines, such as the resource count and any defect found in the schema itself) and the per-resource `records`.

- In `json` format (the default) the report is a single JSON object: `{"summary": [...], "resources": [...]}`. Each resource record carries its `id`, `uuid`, `resource_type`, `title`, `valid` flag, `error_count`, and the list of `errors` (each with `path`, `title`, `validator` and `message`).
- In `csv` format the summary lines are written first as `#`-prefixed comment lines, followed by the table: one row per error, with the resource columns repeated on every row. `error_count` is only included when `--no-error-details` is used, since otherwise it would be repeated on every error row of the same resource, which would make it harder to diff two reports.

## Examples

- **Example 1**: Validate every resource stored in GeoNode, reporting only the invalid ones.

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.settings python manage.py validate_metadata
    ```

- **Example 2**: Validate only the datasets and maps, including the valid ones in the report, and write it to a file.

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.settings python manage.py validate_metadata --resource-type dataset map --include-valid --output /tmp/validation_report.json
    ```

- **Example 3**: Validate two specific resources by id, producing a CSV report.

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.settings python manage.py validate_metadata --id 12,34 --format csv
    ```

- **Example 4**: Validate a schema file against a few sample instance files, without touching the database.

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.settings python manage.py validate_metadata --schema /tmp/my_schema.json --instance /tmp/instance1.json /tmp/instance2.json
    ```
