# Handle GWC tile layers

GeoWebCache (GWC) is a tile caching mechanism that can be used to speed up the rendering of map layers.

The `gwc` management command allows you to manage GWC tile layers for your GeoNode instance.

## Create GWC Tile Layers

To create GWC tile layers for all your GeoNode layers configured within the local GeoServer, 
run the following command:

```bash
DJANGO_SETTINGS_MODULE=geonode.settings python manage.py gwc create --all
```

This will create GWC tile layers for all your GeoNode layers.

In case you want to create GWC tile layers for a specific layer, you can use the `--layer` option followed by the layer name:

```bash
DJANGO_SETTINGS_MODULE=geonode.settings python manage.py gwc create --layer <layer_name>
```

You can specify multiple layers by repeating the `--layer` option:

```bash
DJANGO_SETTINGS_MODULE=geonode.settings python manage.py gwc create --layer <layer_name_1> --layer <layer_name_2>
```

The `gwc create` command is usually quite conservative and will not mess with GWC tile layers if they already exist. 
However, it also accepts the `--force` option, which forces the creation of GWC tile layers even if they already exist.
This may be useful if you want to recreate GWC tile layers for some reason, for example reset GWC tile layers after a GeoServer layer update.

Notice: the `gwc create` command replaces the old `create_tile_layers` command, which is now deprecated and will be removed in a future release.

## Truncate GWC Tile Layers

To truncate GWC tile layers for all your GeoNode layers, run the following command:

```bash
DJANGO_SETTINGS_MODULE=geonode.settings python manage.py gwc truncate --all
```

This will truncate GWC tile layers for all your GeoNode layers.

In case you want to truncate GWC tile layers for one or more specific layers, 
you can use the `--layer` option followed by the layer name:

```bash
DJANGO_SETTINGS_MODULE=geonode.settings python manage.py gwc truncate --layer <layer_name> [--layer <layer_name_2> ...]
```

