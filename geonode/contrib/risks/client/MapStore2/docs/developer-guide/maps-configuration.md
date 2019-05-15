# Map options


# Layers option


## Layer types

 * WMS
 * Bing
 * Google
 * MapQuest
 * OSM
 * TileProvider

### WMS

### Bing

### Google

### MapQuest

### TileProvider
TileProvider is a shortcut to easily configure many different layer sources. 
It's enough to add provider property and 'tileprovider' as type property to the layer configuration object. Property value should be in the form of ProviderName.VariantName.
 
List of available layer [here](https://github.com/geosolutions-it/MapStore2/blob/master/web/client/utils/ConfigProvider.js)

i.e.
> ``{
"type": "tileprovider",
"title": "Title",
"provider": "Stamen.Toner",
"name": "Name",
"group": "GroupName",
"visibility": false
}``

Options passed in configuration object, if already configured by TileProvider,  will be overridden.

Openlayer's TileProvider at the moment doesn't support minZoom configuration property and hi resolution map
