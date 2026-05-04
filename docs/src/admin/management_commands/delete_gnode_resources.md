# Delete Certain GeoNode Resources

The `delete_resources` `Management Command` allows removing resources meeting a certain condition, specified in the form of a serialized Django `Q()` expression.

First of all, let us take a look at the `--help` option of the `delete_resources` management command in order to inspect all the command options and features.

Run:

```bash
DJANGO_SETTINGS_MODULE=geonode.settings python manage.py delete_resources --help
```

!!! Note
    If you enabled `local_settings.py`, the command will change as follows:

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.local_settings python manage.py delete_resources --help
    ```

This produces the following output:

```bash
usage: manage.py delete_resources [-h] [-c CONFIG_PATH]
                                  [-l LAYER_FILTERS [LAYER_FILTERS ...]]
                                  [-m MAP_FILTERS [MAP_FILTERS ...]]
                                  [-d DOCUMENT_FILTERS [DOCUMENT_FILTERS ...]]
                                  [--version] [-v {0,1,2,3}]
                                  [--settings SETTINGS]
                                  [--pythonpath PYTHONPATH] [--traceback]
                                  [--no-color] [--force-color]

Delete resources meeting a certain condition

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_PATH, --config CONFIG_PATH
                        Configuration file path. Default is:
                        delete_resources.json
  -l LAYER_FILTERS [LAYER_FILTERS ...], --layer_filters LAYER_FILTERS [LAYER_FILTERS ...]
  -m MAP_FILTERS [MAP_FILTERS ...], --map_filters MAP_FILTERS [MAP_FILTERS ...]
  -d DOCUMENT_FILTERS [DOCUMENT_FILTERS ...], --document_filters DOCUMENT_FILTERS [DOCUMENT_FILTERS ...]
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
  --force-color         Force colorization of the command output.
```

There are two ways to declare `Q()` expressions filtering which resources should be deleted:

1. With a JSON configuration file, by passing the `-c` argument specifying the path to the JSON configuration file.

    - **Example 1**: Relative path to the config file, relative to `manage.py`

      ```bash
      DJANGO_SETTINGS_MODULE=geonode.settings python manage.py delete_resources -c geonode/base/management/commands/delete_resources.json
      ```

    - **Example 2**: Absolute path to the config file

      ```bash
      DJANGO_SETTINGS_MODULE=geonode.settings python manage.py delete_resources -c /home/User/Geonode/configs/delete_resources.json
      ```

2. With CLI, by passing `-l` `-d` `-m` list arguments for each kind of resource, datasets, documents, and maps.

    - **Example 3**: Delete resources without configuration file

      ```bash
      DJANGO_SETTINGS_MODULE=geonode.settings python manage.py delete_resources -l 'Q(pk__in: [1, 2]) | Q(title__icontains:"italy")' 'Q(owner__name=admin)' -d '*' -m "Q(pk__in=[1, 2])"
      ```

## Configuration File

The JSON configuration file should contain a single `filters` object, which consists of `Dataset`, `map`, and `document` lists. Each list specifies the filter conditions applied to a corresponding queryset, defining which items will be deleted.

The filters are evaluated and directly inserted into Django `.filter()` method, which means the filters occurring as separated list items are treated as an AND condition. To create an OR query, the `|` operator should be used. For more info please check the [Django documentation](https://docs.djangoproject.com/en/3.2/topics/db/queries/#complex-lookups-with-q-objects).

The only exception is passing a list with `'*'`, which causes deleting all the queryset of the resource.

- **Example 4**: Example content of the configuration file, which deletes datasets with IDs `1`, `2`, and `3`, those owned by user `admin`, along with all defined maps.

    ```bash
    {
      "filters": {
      "Dataset": [
          "Q(pk__in=[1, 2, 3]) | Q(title__icontains='italy')",
          "Q(user__name=admin)"
        ],
      "map": ["*"],
      "document": []
      }
    }
    ```

## CLI

The CLI configuration can be specified with `-l` `-d` `-m` list arguments, which in fact are a translation of the configuration JSON file. `-l` `-d` `-m` arguments are evaluated in the same manner as `filters.Dataset`, `filters.map`, and `filter.document` accordingly from Example 4.

The following example result is equivalent to Example 4:

- **Example 5**: Example CLI configuration, which deletes datasets with IDs `1`, `2`, and `3`, along with all maps.

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.settings python manage.py delete_resources -l 'Q(pk__in: [1, 2, 3]) | Q(title__icontains:"italy")' 'Q(owner__name=admin)' -m '*'
    ```
