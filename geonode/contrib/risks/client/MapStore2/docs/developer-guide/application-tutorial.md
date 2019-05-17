Writing a new MapStore2 based application can be done following these steps:
 * create a new folder for the application, inside the MapStore2 directory tree (e.g. web/client/examples/myapp), and the following folder structure:

```
+-- myapp
    +-- index.html
    +-- config.json
    +-- webpack.config.js
    +-- app.jsx
    +-- containers
    |   +-- myapp.jsx
    +-- stores
        +-- myappstore.js
```
 * create an **index.html** file inside the application folder

```html
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="Content-Type" content="text/html;charset=ISO-8859-1">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>MyApp</title>
        <link rel="stylesheet" href="http://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.3/leaflet.css" />
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
        <style>
        html, body, #container, #map {
            position:absolute;
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
        }

        </style>
    </head>
    <body>
        <div id="container"></div>
        <script src="dist/myapp.js"></script>
    </body>
</html>
```
 * create an **app.jsx** for the main app ReactJS component

```javascript
var React = require('react');
var ReactDOM = require('react-dom');

var Provider = require('react-redux').Provider;

// include application component
var MyApp = require('./containers/MyApp');
var url = require('url');

var loadMapConfig = require('../../actions/config').loadMapConfig;
var ConfigUtils = require('../../utils/ConfigUtils');

// initializes Redux store
var store = require('./stores/myappstore');

// reads parameter(s) from the url
const urlQuery = url.parse(window.location.href, true).query;

// get configuration file url (defaults to config.json on the app folder)
const { configUrl, legacy } = ConfigUtils.getConfigurationOptions(urlQuery, 'config', 'json');

// dispatch an action to load the configuration from the config.json file
store.dispatch(loadMapConfig(configUrl, legacy));

// Renders the application, wrapped by the Redux Provider to connect the store to components
ReactDOM.render(
    <Provider store={store}>
        <MyApp />
    </Provider>,
    document.getElementById('container')
);
```
 * create a **myapp.jsx** component inside the **containers** folder, that will contain the all-in-one Smart Component of the application

```javascript
var React = require('react');
var connect = require('react-redux').connect;
var LMap = require('../../../components/map/leaflet/Map');
var LLayer = require('../../../components/map/leaflet/Layer');

var MyApp = React.createClass({
    propTypes: {
        // redux store slice with map configuration (bound through connect to store at the end of the file)
        mapConfig: React.PropTypes.object,
        // redux store dispatch func
        dispatch: React.PropTypes.func
    },
    renderLayers(layers) {
        if (layers) {
            return layers.map(function(layer) {
                return <LLayer type={layer.type} key={layer.name} options={layer} />;
            });
        }
        return null;
    },
    render() {
        // wait for loaded configuration before rendering
        if (this.props.mapConfig && this.props.mapConfig.map) {
            return (
                <LMap id="map" center={this.props.mapConfig.map.center} zoom={this.props.mapConfig.map.zoom}>
                     {this.renderLayers(this.props.mapConfig.layers)}
                </LMap>
            );
        }
        return null;
    }
});

// include support for OSM and WMS layers
require('../../../components/map/leaflet/plugins/OSMLayer');
require('../../../components/map/leaflet/plugins/WMSLayer');

// connect Redux store slice with map configuration
module.exports = connect((state) => {
    return {
        mapConfig: state.mapConfig
    };
})(MyApp);
```

 * create a **myappstore.js** store initalizer inside the **stores** folder, that will create the global Redux store for the application, combining the needed reducers and middleware components

```javascript
var {createStore, combineReducers, applyMiddleware} = require('redux');

var thunkMiddleware = require('redux-thunk');
var mapConfig = require('../../../reducers/config');

 // reducers
const reducers = combineReducers({
    mapConfig
});

// compose middleware(s) to createStore
let finalCreateStore = applyMiddleware(thunkMiddleware)(createStore);

// export the store with the given reducers (and middleware applied)
module.exports = finalCreateStore(reducers, {});
```

 * create a **config.json** file with basic map configuration

```javascript
{
  "map": {
    "projection": "EPSG:900913",
    "units": "m",
    "center": {"x": 1250000.000000, "y": 5370000.000000, "crs": "EPSG:900913"},
    "zoom":5,
    "layers": [
      {
        "type": "osm",
        "title": "Open Street Map",
        "name": "mapnik",
        "group": "background",
        "visibility": true
      },
      {
        "type": "wms",
        "url":"http://demo.geo-solutions.it/geoserver/wms",
        "visibility": true,
        "opacity": 0.5,
        "title": "Weather data",
        "name": "nurc:Arc_Sample",
        "group": "Meteo",
        "format": "image/png"
      }
    ]
  }
}
```

* create a **webpack.config.js** file with build configuration

```javascript
var path = require("path");
var LoaderOptionsPlugin = require("webpack/lib/LoaderOptionsPlugin");

module.exports = {
    entry: {
        myapp: path.join(__dirname, "app")
    },
    output: {
      path: path.join(__dirname, "dist"),
        publicPath: "/dist/",
        filename: "myapp.js"
    },
    resolve: {
      extensions: [".js", ".jsx"]
    },
    module: {
        rules: [
            {
                test: /\.jsx?$/,
                exclude: /node_modules/,
                use: [{
                    loader: "babel-loader"
                }]

            }
        ]
    },
    devtool: 'inline-source-map',
    plugins: [
        new LoaderOptionsPlugin({
            debug: true
        })
    ]
};


```

Now the application is ready, to launch it in development mode, you can use the following command (launch it from the MapStore2 main folder):

```
./node_modules/.bin/webpack-dev-server --config web/client/examples/myapp/webpack.config.js --progress --colors --port 8081 --content-base web/client/examples/myapp
```

Then point your preferred browser to the following url: [http://localhost:8081](http://localhost:8081)
