# Start MapStore2 client in development mode

## Pre-requisites

1. You need a running instance of GeoNode somewhere. In this specific example we assume GeoNode is running on `http://localhost:8000`

## Install needed packages

```bash
sudo apt install nodejs npm
```

## Prepare the source code

```bash
git clone --recursive https://github.com/GeoNode/geonode-mapstore-client.git geonode-mapstore-client-dev
```

## Compile MapStore2 Client

```bash
cd geonode-mapstore-client/geonode_mapstore_client/client/
npm update
npm install
npm run compile
```

## Edit the file `env.json`

```bash
vim env.json
```

```json
{
    "DEV_SERVER_HOST": "localhost:8000",
    "DEV_SERVER_HOST_PROTOCOL": "http"
}
```

## Run MapStore2 in Development mode

```bash
npm run start
```

Connect to `http://localhost:8081`

This is a `proxied` version of GeoNode from MapStore2 client. **To upload new layers use the original GeoNode**.

Every time you render a map, from the GeoNode layer details page or map creation, you will access the MapStore2 dev mode running code.

You can now update the code on the fly.

## Example 1: Disable the PrintPlugin from the Layer Details small map

```bash
vim js/previewPlugins.js
```

```javascript
...
BurgerMenuPlugin: require('../MapStore2/web/client/plugins/BurgerMenu'),
ScaleBoxPlugin: require('../MapStore2/web/client/plugins/ScaleBox'),
MapFooterPlugin: require('../MapStore2/web/client/plugins/MapFooter'),
// PrintPlugin: require('../MapStore2/web/client/plugins/Print'),
TimelinePlugin: require('../MapStore2/web/client/plugins/Timeline'),
PlaybackPlugin: require('../MapStore2/web/client/plugins/Playback'),
...
```

## Example 2: Disable the MousePositionPlugin from the big maps

```bash
vim js/plugins.js
```

```javascript
...
SaveAsPlugin: require('../MapStore2/web/client/plugins/SaveAs').default,
MetadataExplorerPlugin: require('../MapStore2/web/client/plugins/MetadataExplorer'),
GridContainerPlugin: require('../MapStore2/web/client/plugins/GridContainer'),
StyleEditorPlugin: require('../MapStore2/web/client/plugins/StyleEditor'),
TimelinePlugin: require('../MapStore2/web/client/plugins/Timeline'),
PlaybackPlugin: require('../MapStore2/web/client/plugins/Playback'),
// MousePositionPlugin: require('../MapStore2/web/client/plugins/MousePosition'),
SearchPlugin: require('../MapStore2/web/client/plugins/Search'),
SearchServicesConfigPlugin: require('../MapStore2/web/client/plugins/SearchServicesConfig'),
...
```
