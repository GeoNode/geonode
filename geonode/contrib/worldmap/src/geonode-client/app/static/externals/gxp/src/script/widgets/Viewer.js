/**
 * Copyright (c) 2008-2011 The Open Planning Project
 *
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires util.js
 * @requires OpenLayers/Control/Attribution.js
 * @requires OpenLayers/Control/ZoomPanel.js
 * @requires OpenLayers/Control/Navigation.js
 * @requires OpenLayers/Kinetic.js
 * @requires OpenLayers/Control/PanPanel.js
 * @requires GeoExt/widgets/MapPanel.js
 * @requires GeoExt/widgets/ZoomSlider.js
 * @requires GeoExt/widgets/tips/ZoomSliderTip.js
 */

/** api: (define)
 *  module = gxp
 *  class = Viewer
 *  base_link = `Ext.util.Observable <http://extjs.com/deploy/dev/docs/?class=Ext.util.Observable>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: Viewer(config)
 *
 *    A map viewer application framework that can be extended with plugins
 *    for layer sources and tools. Types of viewers that can be built with
 *    this framework range from simple map viewers to complex web-based GIS
 *    applications with capabilities like feature editing, styling and more.
 */
/** api: example
 *    A viewer can be added to an HTML page with a script block containing
 *    something like this for a minimal viewer with an OSM layer:
 *
 *    .. code-block:: javascript
 *
 *      var app = new gxp.Viewer({
 *          sources: {
 *              osm: {
 *                  ptype: "gxp_osmsource"
 *              }
 *          },
 *          map: {
 *              center: [0, 0],
 *              zoom: 2,
 *              layers: [{
 *                  source: "osm",
 *                  name: "mapnik"
 *              }]
 *          }
 *      });
 */
gxp.Viewer = Ext.extend(Ext.util.Observable, {

    /** private: property[mapPanel]
     *  ``GeoExt.MapPanel``
     */

    /** api: config[proxy]
     * ``String`` An optional proxy url which can be used to bypass the same
     * origin policy. This will be set as ``OpenLayers.ProxyHost``.
     */

    /** api: config[mapItems]
     *  ``Array(Ext.Component)``
     *  Any items to be added to the map panel. A typical item to put on a map
     *  would be a ``GeoExt.ZoomSlider``.
     */

    /** api: config[mapPlugins]
     *  ``Array(Ext.util.Observable)``
     *  Any plugins to be added to the map panel, e.g. ``gxp.plugins.LoadingIndicator``.
     */

    /** api: config[portalConfig]
     *  ``Object`` Configuration object for the wrapping container of the
     *  viewer. This will be an ``Ext.Panel`` if it has a ``renderTo``
     *  property, or an ``Ext.Viewport`` otherwise.
     */

    /** api: config[portalItems]
     *  ``Array`` Items for the portal. A MapPanel will automatically be added
     *  to the portal, unless ``portalConfig`` has ``items`` configured.
     */

    /** api: config[sources]
     *  ``Object`` Layer source configurations for this viewer, keyed by source
     *  id. The source id will be used to reference the layer source in the
     *  ``layers`` array of the ``map`` object.
     */

    /** api: config[map]
     *  ``Object`` Map configuration for this viewer. This object is similar
     *  to the ``GeoExt.MapPanel`` configuration, with the following
     *  exceptions:
     *
     *  * center: ``Array`` of lon (x) and lat (y) values
     *  * items: not available - use ``mapItems`` instead
     *  * tbar: not available - use :class:`gxp.Tool` plugins to populate
     *    the tbar
     *  * wrapDateLine: ``Boolean`` Should we wrap the dateline? Defaults to
     *    true
     *  * numZoomLevels: ``Integer`` The number of zoom levels to use.
     *  * layers: ``Array(Object)``. Each object has a ``source`` property
     *    referencing a :class:`gxp.plugins.LayerSource`. The viewer will call
     *    the ``createLayerRecord`` of this source with the object as
     *    argument, which will result in a layer being created with the
     *    configuration provided here.
     *
     *    Valid config options for all layer sources:
     *
     *    * source: ``String`` referencing a source from ``sources``
     *    * name: ``String`` - the name from the source's ``store`` (only for
     *      sources that maintain a store)
     *    * visibility: ``Boolean`` - initial layer visibility
     *    * opacity: ``Number`` - initial layer.opacity
     *    * group: ``String`` - group for the layer when the viewer also uses a
     *      :class:`gxp.plugins.LayerTree`. Set this to "background" to make
     *      the layer a base layer
     *    * fixed: ``Boolean`` - Set to true to prevent the layer from being
     *      removed by a :class:`gxp.plugins.RemoveLayer` tool and from being
     *      dragged in a :class:`gxp.plugins.LayerTree`
     *    * selected: ``Boolean`` - Set to true to mark the layer selected
     *  * map: not available, can be configured with ``maxExtent``,
     *    ``numZoomLevels`` and ``theme``.
     *  * restrictedExtent: ``Array`` to be consumed by
     *    ``OpenLayers.Bounds.fromArray`` - the restrictedExtent of the map
     *  * maxExtent: ``Array`` to be consumed by
     *    ``OpenLayers.Bounds.fromArray`` - the maxExtent of the map
     *  * numZoomLevels: ``Number`` - the number of zoom levels if not
     *    available on the first layer
     *  * theme: ``String`` - optional theme for the ``OpenLayers.Map``, as
     *    in ``OpenLayers.Map.theme``.
     */

    /** api: config[defaultToolType]
     *  ``String``
     *  The default tool plugin type. Default is "gxp_tool"
     */
    defaultToolType: "gxp_tool",

    /** api: config[tools]
     *  ``Array(`` :class:`gxp.plugins.Tool` ``)``
     *  Any tools to be added to the viewer. Tools are plugins that will be
     *  plugged into this viewer's ``portal``. The ``tools`` array is usually
     *  populated with configuration objects for plugins (using a ptype),
     *  rather than instances. A default ptype can be configured with this
     *  viewer's ``defaultToolType`` option.
     */

    /** api: property[tools]
     *  ``Object`` Storage of tool instances for this viewer, keyed by id
     */
    tools: null,

    /** api: config[defaultSourceType]
     *  ``String``
     *  The default layer source plugin type.
     */

    /** api: property[portalItems]
     *  ``Array(Ext.Component)``
     *  Items that make up the portal.
     */

    /** api: property[selectedLayer]
     *  ``GeoExt.data.LayerRecord`` The currently selected layer
     */
    selectedLayer: null,

    /** api: config[field]
     *  :class:`gxp.form.ViewerField` Optional - set by
     *  :class:`gxp.form.ViewerField` so plugins like
     *  :class:`gxp.plugins.FeatureToField` can set the form field's value.
     */

    /** api: property[field]
     *  :class:`gxp.form.ViewerField` Used by plugins to access the form field.
     *  Only available if this viewer is wrapped into an
     *  :class:`Ext.form.ViewerField`.
     */

    /** api: config[authenticate]
     *  ``Function`` A global authentication function that is invoked by
     *  :meth:`doAuthorized` if no user is logged in or the current user is not
     *  authorized. That process is supposed to call :meth:`setAuthorizedRoles`
     *  upon successful authentication, and :meth:`cancelAuthentication` if the
     *  user cancels the login process. Typically this function creates and
     *  opens a login window. Optional, default is null.
     */

    /** api: property[authenticate]
     *  ``Function`` Like the config option above, but this can be set after
     *  configuration e.g. by a plugin that provides authentication. It can
     *  also be accessed to check if an authentication mechanism is available.
     */
    authenticate: null,

    /** api: property[authorizedRoles]
     *  ``Array`` Roles the application is authorized for. This property is
     *  usually set by the :meth:`setAuthorizedRoles` method, which is
     *  typically called by a component that authenticates the user (e.g. a
     *  login window. After authentication, if the client is authorized to do
     *  everything,  this should be set to ``["ROLE_ADMINISTRATOR"]``.
     *
     *  If this property is undefined, the ``isAuthorized()`` method will
     *  return undefined, so plugins can check for that to do their own auth
     *  checks in this case. So if the application uses an authentication
     *  component (e.g. a login window), it is recommended to set this to
     *  ``[]`` (equivalent to "not authorized to do anything") initially.
     */

    /** private: method[constructor]
     *  Construct the viewer.
     */
    constructor: function(config) {

        // add any custom application events
        this.addEvents(
            /** api: event[ready]
             *  Fires when application is ready for user interaction.
             */
            "ready",

            /** api: event[portalready]
             *  Fires after the portal is initialized.
             */
            "portalready",

            /** api: event[beforelayerselectionchange]
             *  Fired before the selected set of layers changes.  Listeners
             *  can return ``false`` to stop the selected layers from being
             *  changed.
             *
             *  Listeners arguments:
             *
             *  * layerRecord - ``GeoExt.data.LayerRecord`` the record of the
             *    selected layer, or null if no layer is selected.
             */
            "beforelayerselectionchange",

            /** api: event[layerselectionchange]
             *  Fired when the selected set of layers changes.
             *
             *  Listeners arguments:
             *
             *  * layerRecord - ``GeoExt.data.LayerRecord`` the record of the
             *    selected layer, or null if no layer is selected.
             */
            "layerselectionchange",

            /** api: event[featureedit]
             *  Fired when features were edited.
             *
             *  Listener arguments:
             *
             *  * featureManager - :class:`gxp.plugins.FeatureManager` the
             *    the feature manager that was used for editing
             *  * layer - ``Object`` object with name and source of the layer
             *    that was edited
             */
            "featureedit",

            /** api: event[authorizationchange]
             *  Fired when the authorizedRoles are changed, e.g. when a user
             *  logs in or out.
             */
            "authorizationchange"
        );

        Ext.apply(this, {
            layerSources: {},
            portalItems: []
        });

        // private array of pending getLayerRecord requests
        this.createLayerRecordQueue = [];

        (config.loadConfig || this.loadConfig).call(this, config, this.applyConfig);
        gxp.Viewer.superclass.constructor.apply(this, arguments);

    },

    /** api: method[selectLayer]
     *  :arg record: ``GeoExt.data.LayerRecord``` Layer record.  Call with no
     *      layer record to remove layer selection.
     *  :returns: ``Boolean`` Layers were set as selected.
     *
     *  TODO: change to selectLayers (plural)
     */
    selectLayer: function(record) {
        record = record || null;
        var changed = false;
        var allow = this.fireEvent("beforelayerselectionchange", record);
        if (allow !== false) {
            changed = true;
            if (this.selectedLayer) {
                this.selectedLayer.set("selected", false);
            }
            this.selectedLayer = record;
            if (this.selectedLayer) {
                this.selectedLayer.set("selected", true);
            }
            this.fireEvent("layerselectionchange", record);
        }
        return changed;
    },

    /** api: method[loadConfig]
     *  :arg config: ``Object`` The config object passed to the constructor.
     *
     *  Subclasses that load config asynchronously can override this to load
     *  any configuration before applyConfig is called.
     */
    loadConfig: function(config) {
        this.applyConfig(config);
    },

    applyConfig: function(config) {
        this.initialConfig = Ext.apply({}, config);
        Ext.apply(this, this.initialConfig);
        this.load();
    },

    load: function() {

        // pass on any proxy config to OpenLayers
        if (this.proxy) {
            OpenLayers.ProxyHost = this.proxy;
        }

        this.initMapPanel();

        this.initTools();

        // initialize all layer source plugins
        var config, queue = [];
        for (var key in this.sources) {
            queue.push(this.createSourceLoader(key));
        }

        // create portal when dom is ready
        queue.push(function(done) {
            Ext.onReady(function() {
                this.initPortal();
                done();
            }, this);
        });

        gxp.util.dispatch(queue, this.activate, this);

    },

    createSourceLoader: function(key) {
        return function(done) {
            var config = this.sources[key];
            config.projection = this.initialConfig.map.projection;
            this.addLayerSource({
                id: key,
                config: config,
                callback: done,
                fallback: function(source, msg, details) {
                    // TODO: log these issues somewhere that the app can display
                    // them after loading.
                    // console.log(arguments);
                    done();
                },
                scope: this
            });
        };
    },

    addLayerSource: function(options) {
        var id = options.id || Ext.id(null, "gxp-source-");
        var source;
        var config = options.config;
        config.id = id;
        try {
            //If there's a ptype in the passed config object, use that instead of the default.
            source = Ext.ComponentMgr.createPlugin(
                options.config, (options.config.ptype? options.config.ptype : this.defaultSourceType)
            );
        } catch (err) {
            throw new Error("Could not create new source plugin with ptype: " + options.config.ptype);
        }
        source.on({
            ready: {
                fn: function() {
                    var callback = options.callback || Ext.emptyFn;
                    callback.call(options.scope || this, id);
                },
                scope: this,
                single: true
            },
            failure: {
                fn: function() {
                    var fallback = options.fallback || Ext.emptyFn;
                    delete this.layerSources[id];
                    fallback.apply(options.scope || this, arguments);
                },
                scope: this,
                single: true
            }
        });
        this.layerSources[id] = source;
        source.init(this);

        return source;
    },

    initMapPanel: function() {

        var config = Ext.apply({}, this.initialConfig.map);
        var mapConfig = {};
        var baseLayerConfig = {
            wrapDateLine: config.wrapDateLine !== undefined ? config.wrapDateLine : true,
            maxResolution: config.maxResolution,
            numZoomLevels: config.numZoomLevels,
            displayInLayerSwitcher: false
        };

        // split initial map configuration into map and panel config
        if (this.initialConfig.map) {
            var props = "theme,controls,resolutions,projection,units,maxExtent,restrictedExtent,maxResolution,numZoomLevels,panMethod".split(",");
            var prop;
            for (var i=props.length-1; i>=0; --i) {
                prop = props[i];
                if (prop in config) {
                    mapConfig[prop] = config[prop];
                    delete config[prop];
                }
            }
        }

        this.mapPanel = Ext.ComponentMgr.create(Ext.applyIf({
            xtype: config.xtype || "gx_mappanel",
            map: Ext.applyIf({
                theme: mapConfig.theme || null,
                controls: mapConfig.controls || [
                    new OpenLayers.Control.Navigation({
                        zoomWheelOptions: {interval: 250},
                        dragPanOptions: {enableKinetic: true}
                    }),
                    new OpenLayers.Control.PanPanel(),
                    new OpenLayers.Control.ZoomPanel(),
                    new OpenLayers.Control.Attribution()
                ],
                maxExtent: mapConfig.maxExtent && OpenLayers.Bounds.fromArray(mapConfig.maxExtent),
                restrictedExtent: mapConfig.restrictedExtent && OpenLayers.Bounds.fromArray(mapConfig.restrictedExtent),
                numZoomLevels: 21
            }, mapConfig),
            center: config.center && new OpenLayers.LonLat(config.center[0], config.center[1]),
            resolutions: config.resolutions,
            forceInitialExtent: true,
            layers: [new OpenLayers.Layer(null, baseLayerConfig)],
            items: this.mapItems,
            plugins: this.mapPlugins,
            tbar: config.tbar || new Ext.Toolbar({
                hidden: true
            })
        }, config));
        this.mapPanel.getTopToolbar().on({
            afterlayout: this.mapPanel.map.updateSize,
            show: this.mapPanel.map.updateSize,
            hide: this.mapPanel.map.updateSize,
            scope: this.mapPanel.map
        });

        this.mapPanel.layers.on({
            "add": function(store, records) {
                // check selected layer status
                var record;
                for (var i=records.length-1; i>= 0; i--) {
                    record = records[i];
                    if (record.get("selected") === true) {
                        this.selectLayer(record);
                    }
                }
            },
            "remove": function(store, record) {
                if (record.get("selected") === true) {
                    this.selectLayer();
                }
            },
            scope: this
        });
    },

    initTools: function() {
        this.tools = {};
        if (this.initialConfig.tools && this.initialConfig.tools.length > 0) {
            var tool;
            for (var i=0, len=this.initialConfig.tools.length; i<len; i++) {
                try {
                    tool = Ext.ComponentMgr.createPlugin(
                        this.initialConfig.tools[i], this.defaultToolType
                    );
                } catch (err) {
                    throw new Error("Could not create tool plugin with ptype: " + this.initialConfig.tools[i].ptype);
                }
                tool.init(this);
            }
        }
    },

    initPortal: function() {

        var config = this.portalConfig || {};

        if (this.portalItems.length === 0) {
            this.mapPanel.region = "center";
            this.portalItems.push(this.mapPanel);
        }

        this.portal = Ext.ComponentMgr.create(Ext.applyIf(config, {
            layout: "fit",
            hideBorders: true,
            items: {
                layout: "border",
                deferredRender: false,
                items: this.portalItems
            }
        }), config.renderTo ? "panel" : "viewport");

        this.fireEvent("portalready");
    },

    activate: function() {
        // initialize tooltips
        Ext.QuickTips.init();
        Ext.apply(Ext.QuickTips.getQuickTip(), {
        	dismissDelay: 0,
        	hideDelay: 5000
        });
        // add any layers from config
        this.addLayers();

        // respond to any queued requests for layer records
        this.checkLayerRecordQueue();

        // broadcast ready state
        this.fireEvent("ready");
    },

    addLayers: function() {
        var mapConfig = this.initialConfig.map;
        var selectedBackground = 0;
        if(mapConfig && mapConfig.layers) {
            var conf, source, record, baseRecords = [], overlayRecords = [];
            for (var i=0; i<mapConfig.layers.length; ++i) {
                conf = mapConfig.layers[i];
                source = this.layerSources[conf.source];
                // source may not have loaded properly (failure handled elsewhere)
                if (source) {
                    record = source.createLayerRecord(conf);
                    if (record) {
                        if (record.get("group") === "background") {
                            baseRecords.push(record);
                        } else {
                            overlayRecords.push(record);
                        }
                    }
                }
            }

            var panel = this.mapPanel;
            var map = panel.map;

            var records = baseRecords.concat(overlayRecords);
            if (records.length) {
                panel.layers.add(records);
            }

        }
    },

    /** api: method[getLayerRecordFromMap]
     *  :arg config: ``Object`` A minimal layer configuration object with source
     *      and name properties.
     *  :returns: ``GeoExt.data.LayerRecord``
     *
     *  Retrieves a layer record from the map.
     */
    getLayerRecordFromMap: function(config) {
        var record = null;
        if (this.mapPanel) {
            this.mapPanel.layers.each(function(rec) {
                if (rec.get("source") == config.source && rec.get("name") == config.name) {
                    record = rec;
                    return false;
                }
            });
        }
        return record;
    },

    /** api: method[createLayerRecord]
     *  :arg config: ``Object`` A minimal layer configuration object with source
     *      and name properties.
     *  :arg callback: ``Function`` A function to be called with the layer
     *      record that corresponds to the given config.
     *  :arg scope: ``Object`` Optional scope for the callback.
     *
     *  Asyncronously retrieves a layer record given a basic layer config.  The
     *  callback will be called as soon as the desired layer source is ready.
     *  This method should only be called to retrieve layer records from sources
     *  configured before the call.
     */
    createLayerRecord: function(config, callback, scope) {
        this.createLayerRecordQueue.push({
            config: config,
            callback: callback,
            scope: scope
        });
        this.checkLayerRecordQueue();
    },

    /** private: method[checkLayerRecordQueue]
     *  Check through createLayerRecord requests to see if any can be satisfied.
     */
    checkLayerRecordQueue: function() {
        var request, source, s, record, called;
        var remaining = [];
        for (var i=0, ii=this.createLayerRecordQueue.length; i<ii; ++i) {
            called = false;
            request = this.createLayerRecordQueue[i];
            s = request.config.source;
            if (s in this.layerSources) {
                source = this.layerSources[s];
                record = source.createLayerRecord(request.config);
                if (record) {
                    // we call this in the next cycle to guarantee that
                    // createLayerRecord returns before callback is called
                    (function(req, rec) {
                        window.setTimeout(function() {
                            req.callback.call(req.scope, rec);
                        }, 0);
                    })(request, record);
                    called = true;
                } else if (source.lazy) {
                    source.store.load({
                        callback: this.checkLayerRecordQueue,
                        scope: this
                    });
                }
            }
            if (!called) {
                remaining.push(request);
            }
        }
        this.createLayerRecordQueue = remaining;
    },

    /** api:method[getSource]
     *  :arg layerRec: ``GeoExt.data.LayerRecord`` the layer to get the
     *      source for.
     */
    getSource: function(layerRec) {
        return layerRec && this.layerSources[layerRec.get("source")];
    },

    /** private: method[getState]
     *  :returns: ``Object`` Representation of the app's current state.
     */
    getState: function() {

        // start with what was originally given
        var state = Ext.apply({}, this.initialConfig);

        // update anything that can change
        var center = this.mapPanel.map.getCenter();
        Ext.apply(state.map, {
            center: [center.lon, center.lat],
            zoom: this.mapPanel.map.zoom,
            layers: []
        });

        // include all layer config
        var sources = {};
        this.mapPanel.layers.each(function(record){
            var layer = record.getLayer();
            if (layer.displayInLayerSwitcher) {
                var id = record.get("source");
                var source = this.layerSources[id];
                if (!source) {
                    throw new Error("Could not find source for layer '" + record.get("name") + "'");
                }
                // add layer
                state.map.layers.push(source.getConfigForRecord(record));
                if (!sources[id]) {
                    sources[id] = source.getState();
                }
            }
        }, this);
        // update sources, adding new ones
        Ext.apply(this.sources, sources);

        //standardize portal configuration to portalConfig
        /*
         if (state.portalItems) {
         //initial config included both portal config and items
         if (state.portalConfig && state.portalConfig.items && state.portalConfig.items.length) {
         //merge arrays of portalItems and portalConfig.items
         for (var items = state.portalItems, i = 0, len = items.length; i < len; i++) {
         var item = items[i];
         if (state.portalConfig.items.indexOf(item) == -1) {
         state.portalConfig.items.push(item);
         }
         }
         }
         else if (state.portalItems && state.portalItems.length) {
         !state.portalConfig && (state.portalConfig = {});
         state.portalConfig.items = state.portalItems;
         }
         }
         */

        //get tool states, for most tools this will be the same as its initial config
        state.tools = [];
        Ext.iterate(this.tools,function(key,val,obj){
            //only get and persist the state if there a tool specific getState method
            if(val.getState != gxp.plugins.Tool.prototype.getState){
                state.tools.push(val.getState());
            }
        });
        return state;
    },

    /** api: method[isAuthorized]
     *  :arg roles: ``String|Array`` optional, default is "ROLE_ADMINISTRATOR".
     *       If an array is provided, this method will return if any of the
     *       roles in the array is authorized.
     *  :returns: ``Boolean`` The user is authorized for the given role.
     *
     *  Returns true if the client is authorized with the provided role.
     *  In cases where the application doesn't explicitly handle authentication,
     *  the user is assumed to be authorized for all roles.  This results in
     *  authentication challenges from the browser when an action requires
     *  credentials.
     */
    isAuthorized: function(roles) {
        /**
         * If the application doesn't support authentication, we expect
         * authorizedRoles to be undefined.  In this case, from the UI
         * perspective, we treat the user as if they are authorized to do
         * anything.  This will result in just-in-time authentication challenges
         * from the browser where authentication credentials are needed.
         * If the application does support authentication, we expect
         * authorizedRoles to be a list of roles for which the user is
         * authorized.
         */
        var authorized = false;
        if (this.authorizedRoles) {
            if (!roles) {
                roles = "ROLE_ADMINISTRATOR";
            }
            if (!Ext.isArray(roles)) {
                roles = [roles];
            }
            for (var i=roles.length-1; i>=0; --i) {
                if (~this.authorizedRoles.indexOf(roles[i])) {
                    authorized = true;
                    break;
                }
            }
        }
        return authorized;
    },

    /** api: method[setAuthorizedRoles]
     *  :arg authorizedRoles: ``Array``
     *
     *  Change the authorized roles.
     */
    setAuthorizedRoles: function(authorizedRoles) {
        this.authorizedRoles = authorizedRoles;
        this.fireEvent("authorizationchange");
    },

    /** api: method[cancelAuthentication]
     *  Cancel an authentication process.
     */
    cancelAuthentication: function() {
        if (this._authFn) {
            this.un("authorizationchange", this._authFn, this);
        }
        this.fireEvent("authorizationchange");
    },

    /** api: method[isAuthenticated]
     *  :returns: ``Boolean`` The user has authenticated.
     *
     *  Determines whether a user has logged in.  In cases where the application
     *  doesn't provide a login dialog, the user will be considered logged in.
     *  In this same case, where components require authentication, the browser
     *  will prompt for credentials when needed.
     */
    isAuthenticated: function(role) {
        /**
         * If the application supports authentication, we expect a list of
         * authorized roles to be set (length zero if user has not logged in).
         * If the application does not support authentication, authorizedRoles
         * should be undefined.  In this case, we return true so that components
         * that require authentication can still be enabled.  This leaves the
         * authentication challenge up to the browser.
         */
        return !this.authorizedRoles || this.authorizedRoles.length > 0;
    },

    /** api: method[doAuthorized]
     *  :param roles: ``Array`` Roles required for invoking the action
     *  :param callback: ``Function`` The action to perform
     *  :param scope: ``Object`` The execution scope for the callback
     *
     *  Performs an action (defined as ``callback`` function), but only if
     *  the user is authorized to perform it. If no user is logged in or the
     *  logged in user is not authorized, the viewer's :meth:`authenticate`
     *  function will be invoked. This method is usually called by plugins.
     */
    doAuthorized: function(roles, callback, scope) {
        if (this.isAuthorized(roles) || !this.authenticate) {
            window.setTimeout(function() { callback.call(scope); }, 0);
        } else {
            this.authenticate();
            this._authFn = function authFn() {
                delete this._authFn;
                this.doAuthorized(roles, callback, scope, true);
            };
            this.on("authorizationchange", this._authFn, this, {single: true});
        }
    },

    /** api: method[destroy]
     */
    destroy: function() {
        //TODO there is probably more that needs to be destroyed
        this.mapPanel.destroy();
        this.portal && this.portal.destroy();
    }

});

(function() {
    // OGC "standardized rendering pixel size"
    OpenLayers.DOTS_PER_INCH = 25.4 / 0.28;
})();
