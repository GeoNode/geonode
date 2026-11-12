# Migrate GeoNode base URL

The `migrate_baseurl` `Management Command` allows you to fix all GeoNode links whenever, for some reason, you need to change the `Domain Name` or `IP Address` of GeoNode.

This **must** also be used when you need to change the network schema from `HTTP` to `HTTPS`, for example.

First, let us look at the `--help` option of the `migrate_baseurl` management command in order to inspect all command options and features.

Run:

```bash
DJANGO_SETTINGS_MODULE=geonode.settings python manage.py migrate_baseurl --help
```

This produces output similar to the following:

```bash
usage: manage.py migrate_baseurl [-h] [--version] [-v {0,1,2,3}]
                                 [--settings SETTINGS]
                                 [--pythonpath PYTHONPATH] [--traceback]
                                 [--no-color] [-f]
                                 [--source-address SOURCE_ADDRESS]
                                 [--target-address TARGET_ADDRESS]

Migrate GeoNode VM Base URL

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
-f, --force           Forces the execution without asking for confirmation.
--source-address SOURCE_ADDRESS
                        Source Address (the one currently on DB e.g.
                        http://192.168.1.23)
--target-address TARGET_ADDRESS
                        Target Address (the one to be changed e.g. http://my-
                        public.geonode.org)
```

- **Example 1**: I want to move my GeoNode instance from `http:\\127.0.0.1` to `http:\\example.org`

    !!! Warning
        Always make sure you are using the **correct** settings.

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.settings python manage.py migrate_baseurl --source-address=127.0.0.1 --target-address=example.org
    ```

- **Example 2**: I want to move my GeoNode instance from `http:\\example.org` to `https:\\example.org`

    !!! Warning
        Always make sure you are using the **correct** settings.

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.settings python manage.py migrate_baseurl --source-address=http:\\example.org --target-address=https:\\example.org
    ```

- **Example 3**: I want to move my GeoNode instance from `https:\\example.org` to `https:\\geonode.example.org`

    !!! Warning
        Always make sure you are using the **correct** settings.

    ```bash
    DJANGO_SETTINGS_MODULE=geonode.settings python manage.py migrate_baseurl --source-address=example.org --target-address=geonode.example.org
    ```

!!! Note
    After migrating the base URL, make sure to sanitize links and catalog metadata as well. See [Update Permissions, Metadata, Legends and Download Links](update_perms_metadata.md).
