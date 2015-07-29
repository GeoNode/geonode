# Exif Contrib App

Exif is a contrib app starting with GeoNode 2.4.  The exif contrib app extracts exif metadata from uploaded JPEG documents.  This contrib app helps automatically fill key metadata gaps, such as the date a picture was taken.  If a document has exif metadata, the exif metadata is visible on a new tab on the document detail page.

Exif data can contain very valuable metadata such as the date and time a picture was taken, the GPS location, and photometric properties.  Not all this metadata is currently used. 

## Settings

### Activation

To activate the exif contrib app, you need to add `geonode.contrib.exif` to `INSTALLED_APPS`.  For example, with:

```Python
GEONODE_CONTRIB_APPS = (
    'geonode.contrib.exif'
)
GEONODE_APPS = GEONODE_APPS + GEONODE_CONTRIB_APPS
```

### Configuration

The relevant section in [settings.py](https://github.com/GeoNode/geonode/blob/master/geonode/settings.py) starts at line [804](https://github.com/GeoNode/geonode/blob/master/geonode/settings.py#L804).

```Python
# Settings for Exif contrib app
EXIF_ENABLED = False
```

To enable the exif contrib app switch `EXIF_ENABLED` to `True`.

## Exif

See the Wikipedia article on Exif at https://en.wikipedia.org/wiki/Exchangeable_image_file_format to learn more.
