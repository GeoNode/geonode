# api_basemaps App

API Basemaps is a contrib app that is automatically loaded in settings.py. It will check if any of the below settings are set and then append them to the MAP_BASELAYERS list. Each value can also be added by setting an environment variable using the variable name shown below.

e.g. ```export ALT_OSM_BASEMAPS=True```

By default all values are set as False.

## Settings

Specific settings for map API providers:

* ALT_OSM_BASEMAPS set this variable to True if you want additional osm basemaps
* CARTODB_BASEMAPS set this variable to True if you want cartodb basemaps
* STAMEN_BASEMAPS set this variable to True if you want stamen basemaps
* THUNDERFOREST_BASEMAPS set this variable to True if you want thunderforest basemaps
* MAPBOX_ACCESS_TOKEN set this variable to your MapBox public token
* BING_API_KEY set this variable to your BING Map Key value
