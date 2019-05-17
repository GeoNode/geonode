# Plugins Architecture

MapStore2 fully embraces both ReactJS and Redux concepts, enhancing them with the **plugin** concept.

A plugin in MapStore2 is a smart ReactJS component that is:

 * **connected** to a Redux store, so that some properties are automatically wired to the standard MapStore2 state
 * **wired** to standard actions for common events

In addition a plugin:

 * declares some **reducers** that need to be added to the Redux store, if needed
 * declares some **epics** that need to be added to the redux-observable middleare, if needed
 * is fully **configurable** to be easily customized to a certain level

## Building an application using plugins
To use plugins you need to:

 * declare available (required) plugins, properly requiring them from the root application component
 * load / declare plugins configuration
 * create a store that dynamically includes plugins required reducers
 * use a PluginsContainer component as the container for your plugins enabled application slice (can be the whole application or just a part of it)

### Declare available plugins
Create a plugins.js file where you declare all the needed plugins:

plugins.js:

```javascript
module.exports = {
    plugins: {
        MyPlugin: require('../plugins/My')
    },
    requires: {}
};
```

### Load / Create plugins configuration object
Use pluginsConfig.json to configure your plugins.

pluginsConfig.json:

```javascript
{
    ...
    "standard": [
        {
            "name": "Map",
            "cfg": {
                "zoomControl": false,
                "tools": ["locate"]
            }
        },
        ...
    ],
    ...
}
```

### Declare a plugins compatible Redux Store
Create a store that properly initializes plugins reducers and epics (see [standardStore.js](https://github.com/geosolutions-it/MapStore2/blob/master/web/client/stores/StandardStore.js)) :

store.js:

```javascript
const {combineReducers} = require('../utils/PluginsUtils');
const {createDebugStore} = require('../utils/DebugUtils');

module.exports = (plugins) => {
  const allReducers = combineReducers(plugins, {
     ...
  });
  return createDebugStore(allReducers, {});
};
```

### Use a PluginContainer to render all your plugins
In the root application component require plugins declaration and configuration  and use them to initialize both the store and a PluginsContainer (see our [PluginContainer.jsx](https://github.com/geosolutions-it/MapStore2/blob/master/web/client/components/plugins/PluginsContainer.jsx)):

App.jsx:

```javascript
const {pluginsDef} = require('./plugins.js');
const pluginsCfg = require('./pluginsConfig.json');

const store = require('./store')(pluginsDef);

const plugins = PluginsUtils.getPlugins(pluginsDef);

ReactDOM.render(<PluginsContainer plugins={plugins} mode="standard" pluginsConfig={pluginsCfg}/>, ...container...);
```

## Developing a plugin
An example is better than a thousand words:

My.jsx:

```javascript

// this is a dumb component
const MyComponent = require('../components/MyComponent');
const {connect} = require('react-redux');

// let's wire it to state and actions
const MyPlugin = connect((state) => ({
   myproperty: state.myreducer.property
}), {
   myaction
})(MyComponent);

// let's export the plugin and a set of required reducers
const myreducer = require('../reducers/myreducer');
module.exports = {
   MyPlugin,
   reducers: {myreducer}
};
```

## The Plugins Example Application
The [example](http://dev.mapstore2.geo-solutions.it/mapstore/examples/plugins/) shows the plugins infrastructure power in an interactive way.

The UI allows to add / remove plugins from the base applications, and to configure them using a JSON object with plugins configuration properties.
