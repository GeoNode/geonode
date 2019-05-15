/*
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ReactDOM = require('react-dom');

const StandardApp = require('../components/app/StandardApp');
const LocaleUtils = require('../utils/LocaleUtils');
const {connect} = require('react-redux');

const {configureMap, loadMapConfig} = require('../actions/config');

const url = require('url');

const ThemeUtils = require('../utils/ThemeUtils');

const assign = require('object-assign');

require('./mapstore2.css');

const defaultConfig = {
    "map": {
        "projection": "EPSG:3857",
        "units": "m",
        "center": {"x": 1250000.000000, "y": 5370000.000000, "crs": "EPSG:900913"},
        "zoom": 5,
        "maxExtent": [
            -20037508.34, -20037508.34,
            20037508.34, 20037508.34
        ],
        "layers": [{
            "type": "osm",
            "title": "Open Street Map",
            "name": "mapnik",
            "source": "osm",
            "group": "background",
            "visibility": true
        },
        {
            "type": "tileprovider",
            "title": "NASAGIBS Night 2012",
            "provider": "NASAGIBS.ViirsEarthAtNight2012",
            "name": "Night2012",
            "source": "nasagibs",
            "group": "background",
            "visibility": false
        },
        {
            "type": "wms",
            "url": "http://www.realvista.it/reflector/open/service",
            "visibility": false,
            "title": "e-Geos Ortofoto RealVista 1.0",
            "name": "rv1",
            "group": "background",
            "format": "image/jpeg"
        },
        {
            "type": "wms",
            "url": "https://demo.geo-solutions.it/geoserver/wms",
            "visibility": false,
            "title": "Natural Earth",
            "name": "sde:NE2_HR_LC_SR_W_DR",
            "group": "background",
            "format": "image/png"
        },
        {
            "type": "wms",
            "url": "https://demo.geo-solutions.it/geoserver/wms",
            "visibility": false,
            "title": "Hypsometric",
            "name": "sde:HYP_HR_SR_OB_DR",
            "group": "background",
            "format": "image/png"
        },
        {
            "type": "wms",
            "url": "https://demo.geo-solutions.it/geoserver/wms",
            "visibility": false,
            "title": "Gray Earth",
            "name": "sde:GRAY_HR_SR_OB_DR",
            "group": "background",
            "format": "image/png"
        },
        {
            "type": "wms",
            "url": "https://demo.geo-solutions.it/geoserver/wms",
            "visibility": true,
            "opacity": 0.5,
            "title": "Weather data",
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png"
        },
        {
            "type": "tileprovider",
            "title": "OpenTopoMap",
            "provider": "OpenTopoMap",
            "name": "OpenTopoMap",
            "source": "OpenTopoMap",
            "group": "background",
            "visibility": false
        }]
    }
};

const defaultPlugins = {
    "mobile": ["Map"],
    "desktop": [
          "Map",
          "Help",
          "Share",
          "DrawerMenu",
          "Identify",
          "Locate",
          "TOC",
          "BackgroundSwitcher",
          "Measure",
          "MeasureResults",
          "Print",
          "ShapeFile",
          "Settings",
          "MetadataExplorer",
          "MousePosition",
          "Toolbar",
          "ScaleBox",
          "ZoomAll",
          "MapLoading",
          "Snapshot",
          "ZoomIn",
          "ZoomOut",
          "Login",
          "OmniBar",
          "BurgerMenu",
          "Expander",
          "Undo",
          "Redo"
    ]
};

function mergeDefaultConfig(pluginName, cfg) {
    var propertyName;
    var i;
    var result;
    for (i = 0; i < defaultPlugins.desktop.length; i++) {
        if (defaultPlugins.desktop[i].name === pluginName) {
            result = defaultPlugins.desktop[i].cfg;
            for (propertyName in cfg) {
                if (cfg.hasOwnProperty(propertyName)) {
                    result[propertyName] = cfg[propertyName];
                }
            }
            return result;
        }
    }
    return cfg;
}

function loadConfigFromStorage(name = 'mapstore.embedded') {
    if (name) {
        const loaded = localStorage.getItem(name);
        if (loaded) {
            return JSON.parse(loaded);
        }
    }
    return null;
}

function getParamFromRequest(paramName) {
    const urlQuery = url.parse(window.location.href, true).query;
    return urlQuery[paramName] || null;
}

function buildPluginsCfg(plugins, cfg) {
    var pluginsCfg = [];
    var i;
    for (i = 0; i < plugins.length; i++) {
        if (cfg[plugins[i] + "Plugin"]) {
            pluginsCfg.push({
                name: plugins[i],
                cfg: mergeDefaultConfig(plugins[i], cfg[plugins[i] + "Plugin"])
            });
        } else {
            pluginsCfg.push({
                name: plugins[i],
                cfg: mergeDefaultConfig(plugins[i], {})
            });
        }
    }
    return {
        mobile: pluginsCfg,
        desktop: pluginsCfg
    };
}

const actionListeners = {};
let stateChangeListeners = [];
let app;

const getInitialActions = (options) => {
    if (!options.initialState) {
        if (options.configUrl) {
            return [loadMapConfig.bind(null, options.configUrl || defaultConfig)];
        }
        return [configureMap.bind(null, options.config || defaultConfig)];
    }
    return [];
};


/**
 * MapStore2 JavaScript API. Allows embedding MapStore2 functionalities into
 * a standard HTML page.
 * @class
 */
const MapStore2 = {
    /**
     * Instantiates an embedded MapStore2 application in the given container.
     * @memberof MapStore2
     * @static
     * @param {string} container id of the DOM element that should contain the embedded MapStore2
     * @param {object} options set of options of the embedded app
     *
     * The options object can contain the following properties, to configure the app UI and state:
     *  * **plugins**: list of plugins (and the related configuration) to be included in the app
     *    look at [Plugins documentation](./plugins-documentation) for further details
     *  * **config**: map configuration object for the application (look at [Map Configuration](./maps-configuration) for details)
     *  * **configUrl**: map configuration url for the application (look at [Map Configuration](./maps-configuration) for details)
     *  * **initialState**: allows setting the initial application state (look at [State Configuration](./app-state-configuration) for details)
     *
     * Styling can be configured either using a **theme**, or a complete custom **less stylesheet**, using the
     * following options properties:
     *  * **style**: less style to be applied
     *  * **theme**: theme configuration options:
     *    * path: path/url of the themes folder related to the current page
     *    * theme: theme name to be used
     *
     * ```javascript
     * {
     *      plugins: ['Map', 'ZoomIn', 'ZoomOut'],
     *      config: {
     *          map: {
     *              ...
     *          }
     *      },
     *      configUrl: '...',
     *      initialState: {
     *          defaultState: {
     *              ...
     *          }
     *      },
     *      style: '<custom style>',
     *      theme: {
     *          theme: 'mytheme',
     *          path: 'dist/themes'
     *      }
     * }
     * ```
     * @example
     * MapStore2.create('container', {
     *      plugins: ['Map']
     * });
     */
    create(container, options) {
        const embedded = require('../containers/Embedded');

        const {initialState, storeOpts} = options;

        const pluginsDef = require('./plugins');
        const pages = [{
            name: "embedded",
            path: "/",
            component: embedded,
            pageConfig: {
                pluginsConfig: options.plugins || defaultPlugins
            }
        }];

        const StandardRouter = connect((state) => ({
            locale: state.locale || {},
            pages
        }))(require('../components/app/StandardRouter'));

        const appStore = require('../stores/StandardStore').bind(null, initialState || {}, {}, {});
        const initialActions = getInitialActions(options);
        const appConfig = {
            storeOpts: assign({}, storeOpts, {notify: true}),
            appStore,
            pluginsDef,
            initialActions,
            appComponent: StandardRouter,
            printingEnabled: false
        };
        if (options.style) {
            let dom = document.getElementById('custom_theme');
            if (!dom) {
                dom = document.createElement('style');
                dom.id = 'custom_theme';
                document.head.appendChild(dom);
            }
            ThemeUtils.renderFromLess(options.style, 'custom_theme', 'themes/default/');
        }
        const defaultThemeCfg = {
          prefixContainer: '#' + container
        };

        const themeCfg = options.theme && assign({}, defaultThemeCfg, options.theme) || defaultThemeCfg;
        app = ReactDOM.render(<StandardApp themeCfg={themeCfg} className="fill" {...appConfig}/>, document.getElementById(container));
        app.store.addActionListener((action) => {
            (actionListeners[action.type] || []).concat(actionListeners['*'] || []).forEach((listener) => {
                listener.call(null, action);
            });
        });
        app.store.subscribe(() => {
            stateChangeListeners.forEach(({listener, selector}) => {
                listener.call(null, selector(app.store.getState()));
            });
        });
    },
    buildPluginsCfg,
    getParamFromRequest,
    loadConfigFromStorage,
    /**
     * Adds a listener that will be notified of all the MapStore2 events (**actions**), or only some of them.
     *
     * @memberof MapStore2
     * @static
     * @param {string} type type of actions to be captured (* for all)
     * @param {function} listener function to be called for each launched action; it will receive
     *  the action as the only argument
     * @example
     * MapStore2.onAction('CHANGE_MAP_VIEW', function(action) {
     *      console.log(action.zoom);
     * });
     */
    onAction: (type, listener) => {
        const listeners = actionListeners[type] || [];
        listeners.push(listener);
        actionListeners[type] = listeners;
    },
    /**
     * Removes an action listener.
     *
     * @memberof MapStore2
     * @static
     * @param {string} type type of actions that is captured by the listener (* for all)
     * @param {function} listener listener to be removed
     * @example
     * MapStore2.offAction('CHANGE_MAP_VIEW', listener);
     */
    offAction: (type, listener) => {
        const listeners = (actionListeners[type] || []).filter((l) => l !== listener);
        actionListeners[type] = listeners;
    },
    /**
     * Adds a listener that will be notified of each state update.
     *
     * @memberof MapStore2
     * @static
     * @param {function} listener function to be called for each state udpate; it will receive
     *  the new state as the only argument
     * @param {function} [selector] optional function that will produce a partial/derived state
     * from the global state before calling the listeners
     * @example
     * MapStore2.onStateChange(function(map) {
     *      console.log(map.zoom);
     * }, function(state) {
     *      return (state.map && state.map.present) || state.map || {};
     * });
     */
    onStateChange: (listener, selector = (state) => state) => {
        stateChangeListeners.push({listener, selector});
    },
    /**
     * Removes a state listener.
     *
     * @memberof MapStore2
     * @static
     * @param {function} listener listener to be removed
     * @example
     * MapStore2.offStateChange(listener);
     */
    offStateChange: (listener) => {
        stateChangeListeners = stateChangeListeners.filter((l) => l !== listener);
    }
};

if (!global.Intl ) {
    // Ensure Intl is loaded, then call the given callback
    LocaleUtils.ensureIntl();
}

module.exports = MapStore2;
