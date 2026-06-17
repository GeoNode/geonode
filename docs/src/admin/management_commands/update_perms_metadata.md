# Update Permissions, Metadata, Legends and Download Links

The following utility `Management Commands` allow you to fix:

1. `Users/Groups Permissions` on `Datasets`; those are refreshed and synchronized with the `GIS Server` ones as well.
2. `Metadata`, `Legend`, and `Download` links on `Datasets` and `Maps`.
3. Cleanup of `Duplicated Links` and `Outdated Thumbnails`.

## Management Command `sync_geonode_datasets`

This command allows you to sync already existing permissions on datasets. To change or set dataset permissions, refer to the relevant batch permissions workflow instead.

The options are:

- **filter**: only update datasets whose names match the given filter.
- **username**: only update data owned by the specified username.
- **updatepermissions**: update dataset permissions and synchronize them back to the GeoSpatial Server. This option is also available from the `Layer Details` page.
- **updateattributes**: update dataset attributes and synchronize them back to the GeoSpatial Server. This option is also available from the `Layer Details` page.
- **updatethumbnails**: update the dataset thumbnail. This option is also available from the `Layer Details` page.
- **updatebbox**: update the dataset BBOX and LatLon BBOX. This option is also available from the `Layer Details` page.
- **remove-duplicates**: remove duplicated links.

First, let us look at the `--help` option of the `sync_geonode_datasets` management command in order to inspect all command options and features.

Run:

```bash
DJANGO_SETTINGS_MODULE=geonode.settings python manage.py sync_geonode_datasets --help
```

!!! Note
    If you enabled `local_settings.py`, the command becomes:

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.local_settings python manage.py sync_geonode_datasets --help
    ```

This produces output similar to the following:

```bash
usage: manage.py sync_geonode_datasets [-h] [--version] [-v {0,1,2,3}]
                                    [--settings SETTINGS]
                                    [--pythonpath PYTHONPATH] [--traceback]
                                    [--no-color] [-i] [-d] [-f FILTER]
                                    [-u USERNAME] [--updatepermissions]
                                    [--updatethumbnails] [--updateattributes][--updatebbox]

Update the GeoNode Datasets: permissions (including GeoFence database),
statistics, thumbnails

optional arguments:
-h, --help            show this help message and exit
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
-i, --ignore-errors   Stop after any errors are encountered.
-d, --remove-duplicates
                        Remove duplicates first.
-f FILTER, --filter FILTER
                        Only update data the Datasets that match the given
                        filter.
-u USERNAME, --username USERNAME
                        Only update data owned by the specified username.
--updatepermissions   Update the Dataset permissions.
--updatethumbnails    Update the Dataset styles and thumbnails.
--updateattributes    Update the Dataset attributes.
--updatebbox          Update the Dataset BBOX.
```

- **Example 1**: I want to update or sync all dataset permissions and attributes with the GeoSpatial Server.

    !!! Warning
        Always make sure you are using the **correct** settings.

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.settings python manage.py sync_geonode_datasets --updatepermissions --updateattributes
    ```

- **Example 2**: I want to regenerate the thumbnails of all datasets belonging to `afabiani`.

    !!! Warning
        Always make sure you are using the **correct** settings.

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.settings python manage.py sync_geonode_datasets -u afabiani --updatethumbnails
    ```

## Management Command `sync_geonode_maps`

This command is similar to the previous one, but it affects `Maps` with some limitations.

The options are:

- **filter**: only update map titles that match the given filter.
- **username**: only update data owned by the specified username.
- **updatethumbnails**: update map styles and thumbnails. This option is also available from the `Map Details` page.
- **remove-duplicates**: remove duplicated links.

First, let us look at the `--help` option of the `sync_geonode_maps` management command in order to inspect all command options and features.

Run:

```bash
DJANGO_SETTINGS_MODULE=geonode.settings python manage.py sync_geonode_maps --help
```

!!! Note
    If you enabled `local_settings.py`, the command becomes:

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.local_settings python manage.py sync_geonode_maps --help
    ```

This produces output similar to the following:

```bash
usage: manage.py sync_geonode_maps [-h] [--version] [-v {0,1,2,3}]
                                [--settings SETTINGS]
                                [--pythonpath PYTHONPATH] [--traceback]
                                [--no-color] [-i] [-d] [-f FILTER]
                                [-u USERNAME] [--updatethumbnails]

Update the GeoNode maps: permissions, thumbnails

optional arguments:
-h, --help            show this help message and exit
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
-i, --ignore-errors   Stop after any errors are encountered.
-d, --remove-duplicates
                        Remove duplicates first.
-f FILTER, --filter FILTER
                        Only update data the maps that match the given filter.
-u USERNAME, --username USERNAME
                        Only update data owned by the specified username.
--updatethumbnails    Update the map styles and thumbnails.
```

- **Example 1**: I want to regenerate the thumbnail of the map `This is a test Map`.

    !!! Warning
        Always make sure you are using the **correct** settings.

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.settings python manage.py sync_geonode_maps --updatethumbnails -f 'This is a test Map'
    ```

## Management Command `set_all_datasets_metadata`

This command allows you to reset `Metadata Attributes` and `Catalogue Schema` on datasets. It also updates the `CSW Catalogue` XML and GeoNode links.

The options are:

- **filter**: only update datasets that match the given filter.
- **username**: only update data owned by the specified username.
- **remove-duplicates**: update map styles and thumbnails.
- **delete-orphaned-thumbs**: remove duplicated links.
- **set-uuid**: refresh the UUID based on the `UUID_HANDLER` if configured. Default is `False`.
- **set_attrib**: if set, refresh the attributes of the resource from GeoServer. Default is `True`.
- **set_links**: if set, refresh the links of the resource. Default is `True`.

First, let us look at the `--help` option of the `set_all_datasets_metadata` management command in order to inspect all command options and features.

Run:

```bash
DJANGO_SETTINGS_MODULE=geonode.settings python manage.py set_all_datasets_metadata --help
```

!!! Note
    If you enabled `local_settings.py`, the command becomes:

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.local_settings python manage.py set_all_datasets_metadata --help
    ```

This produces output similar to the following:

```bash
usage: manage.py set_all_datasets_metadata [-h] [--version] [-v {0,1,2,3}]
                                        [--settings SETTINGS]
                                        [--pythonpath PYTHONPATH]
                                        [--traceback] [--no-color] [-i] [-d]
                                        [-t] [-f FILTER] [-u USERNAME]

Resets Metadata Attributes and Schema to All Datasets

optional arguments:
-h, --help            show this help message and exit
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
-i, --ignore-errors   Stop after any errors are encountered.
-d, --remove-duplicates
                        Remove duplicates first.
-t, --delete-orphaned-thumbs
                        Delete Orphaned Thumbnails.
-f FILTER, --filter FILTER
                        Only update data the Datasets that match the given
                        filter
-u USERNAME, --username USERNAME
                        Only update data owned by the specified username
```

- **Example 1**: After changing the base URL, I want to regenerate the entire catalogue schema and remove duplicates if needed.

    !!! Warning
        Always make sure you are using the **correct** settings.

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.settings python manage.py set_all_datasets_metadata -d
    ```

## Management Command `regenerate_xml`

This command regenerates the `CSW Catalogue` XML metadata files.

The main options are:

- **layer**: only process specified layers.
- **dry-run**: do not actually perform any change.

When run with the `--help` option, the full list of available options is presented.

```bash
DJANGO_SETTINGS_MODULE=geonode.settings python manage.py regenerate_xml --help
```

This produces the following output:

```bash
usage: manage.py regenerate_xml [-h] [-l LAYERS] [--skip-logger-setup] [-d] [--version] [-v {0,1,2,3}] [--settings SETTINGS] [--pythonpath PYTHONPATH] [--traceback] [--no-color] [--force-color]
                            [--skip-checks]

Re-create XML metadata documents

options:
-h, --help            show this help message and exit
-l LAYERS, --layer LAYERS
                        Only process specified layers
--skip-logger-setup   Skips setup of the "geonode.br" logger, "br" handler and "br" format if not present in settings
-d, --dry-run         Do not actually perform any change
--version             Show program's version number and exit.
-v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output
--settings SETTINGS   The Python path to a settings module, e.g. "myproject.settings.main". If this isn't provided, the DJANGO_SETTINGS_MODULE environment variable will be used.
--pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".
--traceback           Raise on CommandError exceptions.
--no-color            Don't colorize the command output.
--force-color         Force colorization of the command output.
--skip-checks         Skip system checks.
```

- **Example**:

    !!! Warning
        Make sure you are using the **correct** settings.

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.settings python manage.py regenerate_xml -d
    ```
