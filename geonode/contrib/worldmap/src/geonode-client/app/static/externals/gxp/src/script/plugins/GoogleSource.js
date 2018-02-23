/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/LayerSource.js
 * @requires OpenLayers/Layer/Google/v3.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = GoogleSource
 */

/** api: (extends)
 *  plugins/LayerSource.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: GoolgeSource(config)
 *
 *    Plugin for using Google layers with :class:`gxp.Viewer` instances. The
 *    plugin uses the GMaps v3 API and also takes care of loading the
 *    required Google resources.
 *
 *    Available layer names for this source are "ROADMAP", "SATELLITE",
 *    "HYBRID" and "TERRAIN"
 */
/** api: example
 *  The configuration in the ``sources`` property of the :class:`gxp.Viewer` is
 *  straightforward:
 *
 *  .. code-block:: javascript
 *
 *    "google": {
 *        ptype: "gxp_google"
 *    }
 *
 *  A typical configuration for a layer from this source (in the ``layers``
 *  array of the viewer's ``map`` config option would look like this:
 *
 *  .. code-block:: javascript
 *
 *    {
 *        source: "google",
 *        name: "TERRAIN"
 *    }
 *
 */
gxp.plugins.GoogleSource = Ext.extend(gxp.plugins.LayerSource, {

    /** api: ptype = gxp_googlesource */
    ptype: "gxp_googlesource",

    /** config: config[timeout]
     *  ``Number``
     *  The time (in milliseconds) to wait before giving up on the Google Maps
     *  script loading.  This layer source will not be availble if the script
     *  does not load within the given timeout.  Default is 7000 (seven seconds).
     */
    timeout: 7000,

    /** api: property[store]
     *  ``GeoExt.data.LayerStore`` containing records with "ROADMAP",
     *  "SATELLITE", "HYBRID" and "TERRAIN" name fields.
     */

    /** api: config[title]
     *  ``String``
     *  A descriptive title for this layer source (i18n).
     */
    title: "Google Layers",

    /** api: config[roadmapAbstract]
     *  ``String``
     *  Description of the ROADMAP layer (i18n).
     */
    roadmapAbstract: "Show street map",

    /** api: config[satelliteAbstract]
     *  ``String``
     *  Description of the SATELLITE layer (i18n).
     */
    satelliteAbstract: "Show satellite imagery",

    /** api: config[hybridAbstract]
     *  ``String``
     *  Description of the HYBRID layer (i18n).
     */
    hybridAbstract: "Show imagery with street names",

    /** api: config[terrainAbstract]
     *  ``String``
     *  Description of the TERRAIN layer (i18n).
     */
    terrainAbstract: "Show street map with terrain",

    /** api: config[roadmapTitle]
     *  ``String``
     *  Title of the ROADMAP layer (i18n).
     */
    roadmapTitle: "Google Roadmap",
    
    /** api: config[hybridTitle]
     *  ``String``
     *  Title of the HYBRID layer (i18n).
     */
    hybridTitle: "Google Hybrid",
    
    /** api: config[satelliteTitle]
     *  ``String``
     *  Title of the SATELLITE layer (i18n).
     */
    satelliteTitle: "Google Satellite",
    
    /** api: config[terrainTitle]
     *  ``String``
     *  Title of the TERRAIN layer (i18n).
     */
    terrainTitle: "Google Terrain",
    
    
    /** api: config[otherParams]
     *  ``String``
     *  Additional parameters to be sent to Google,
     *  default is "sensore=false"
     */
    otherParams: "sensor=false",

    constructor: function(config) {
        this.config = config;
        gxp.plugins.GoogleSource.superclass.constructor.apply(this, arguments);
    },

    /** api: method[createStore]
     *
     *  Creates a store of layer records.  Fires "ready" when store is loaded.
     */
    createStore: function() {
        gxp.plugins.GoogleSource.loader.onLoad({
            otherParams: this.otherParams,
            timeout: this.timeout,
            callback: this.syncCreateStore,
            errback: function() {
                delete this.store;
                this.fireEvent(
                    "failure",
                    this,
                    "The Google Maps script failed to load within the provided timeout (" + (this.timeout / 1000) + " s)."
                );
            },
            scope: this
        });
    },

    /** private: method[syncCreateStore]
     *
     *  Creates a store of layers.  This requires that the API script has already
     *  loaded.  Fires the "ready" event when the store is loaded.
     */
    syncCreateStore: function() {
        // TODO: The abstracts ("alt" properties) should be derived from the
        // MapType objects themselves.  It doesn't look like there is currently
        // a way to get the default map types before creating a map object.
        // http://code.google.com/p/gmaps-api-issues/issues/detail?id=2562
        // TODO: We may also be able to determine the MAX_ZOOM_LEVEL for each
        // layer type. If not, consider setting them on the OpenLayers level.
        var mapTypes = {
            "ROADMAP": {"abstract": this.roadmapAbstract, MAX_ZOOM_LEVEL: 20, "title": this.roadmapTitle},
            "SATELLITE": {"abstract": this.satelliteAbstract, "title": this.satelliteTitle},
            "HYBRID": {"abstract": this.hybridAbstract, "title": this.hybridTitle},
            "TERRAIN": {"abstract": this.terrainAbstract, MAX_ZOOM_LEVEL: 15, "title": this.terrainTitle}
        };

        var layers = [];
        var name, mapType;
        for (name in mapTypes) {
            mapType = google.maps.MapTypeId[name];
            layers.push(new OpenLayers.Layer.Google(
                // TODO: get MapType object name
                // http://code.google.com/p/gmaps-api-issues/issues/detail?id=2562
            		mapTypes[name]["title"], {
                    type: mapType,
                    typeName: name,
                    MAX_ZOOM_LEVEL: mapTypes[name].MAX_ZOOM_LEVEL,
                    maxExtent: new OpenLayers.Bounds(-20037508.34,-20037508.34,20037508.34,20037508.34),
                    restrictedExtent: new OpenLayers.Bounds(-20037508.34,-20037508.34,20037508.34,20037508.34),
                    projection: this.projection
                }
            ));
        }
        this.store = new GeoExt.data.LayerStore({
            layers: layers,
            fields: [
                {name: "source", type: "string"},
                {name: "name", type: "string", mapping: "typeName"},
                {name: "abstract", type: "string"},
                {name: "group", type: "string", defaultValue: "background"},
                {name: "fixed", type: "boolean", defaultValue: true},
                {name: "selected", type: "boolean"}
            ]
        });
        this.store.each(function(l) {
            l.set("abstract", mapTypes[l.get("name")]["abstract"]);
        });
        this.fireEvent("ready", this);
    },

    /** api: method[createLayerRecord]
     *  :arg config:  ``Object``  The application config for this layer.
     *  :returns: ``GeoExt.data.LayerRecord``
     *
     *  Create a layer record given the config.
     */
    createLayerRecord: function(config) {
        var record;
        var cmp = function(l) {
            return l.get("name") === config.name;
        };
        // only return layer if app does not have it already
        if (this.target.mapPanel.layers.findBy(cmp) == -1) {
            // records can be in only one store
            record = this.store.getAt(this.store.findBy(cmp)).clone();
            var layer = record.getLayer();
            // set layer title from config
            if (config.title) {
                /**
                 * Because the layer title data is duplicated, we have
                 * to set it in both places.  After records have been
                 * added to the store, the store handles this
                 * synchronization.
                 */
                layer.setName(config.title);
                record.set("title", config.title);
            }
            // set visibility from config
            if ("visibility" in config) {
                layer.visibility = config.visibility;
            }

            record.set("selected", config.selected || false);
            record.set("source", config.source);
            record.set("name", config.name);
            if ("group" in config) {
                record.set("group", config.group);
            }
            record.commit();
        }
        return record;
    }

});

/**
 * Create a loader singleton that all plugin instances can use.
 */
gxp.plugins.GoogleSource.loader = new (Ext.extend(Ext.util.Observable, {

    /** private: property[ready]
     *  ``Boolean``
     *  This plugin type is ready to use.
     */
    ready: !!(window.google && google.maps),

    /** private: property[loading]
     *  ``Boolean``
     *  The resources for this plugin type are loading.
     */
    loading: false,

    constructor: function() {
        this.addEvents(
            /** private: event[ready]
             *  Fires when this plugin type is ready.
             */
             "ready",

             /** private: event[failure]
              *  Fires when script loading fails.
              */
              "failure"
        );
        return Ext.util.Observable.prototype.constructor.apply(this, arguments);
    },

    /** private: method[onScriptLoad]
     *  Called when all resources required by this plugin type have loaded.
     */
    onScriptLoad: function() {
        // the google loader calls this in the window scope
        var monitor = gxp.plugins.GoogleSource.loader;
        if (!monitor.ready) {
            monitor.ready = true;
            monitor.loading = false;
            monitor.fireEvent("ready");
        }
    },

    /** api: method[gxp.plugins.GoogleSource.loader.onLoad]
     *  :arg options: ``Object``
     *
     *  Options:
     *
     *  * callback - ``Function`` Called when script loads.
     *  * errback - ``Function`` Called if loading fails.
     *  * timeout - ``Number`` Time to wait before deciding that loading failed
     *      (in milliseconds).
     *  * scope - ``Object`` The ``this`` object for callbacks.
     */
    onLoad: function(options) {
        if (this.ready) {
            // call this in the next turn for consistent return before callback
            window.setTimeout(function() {
                options.callback.call(options.scope);
            }, 0);
        } else if (!this.loading) {
            this.loadScript(options);
        } else {
            this.on({
                ready: options.callback,
                failure: options.errback || Ext.emptyFn,
                scope: options.scope
            });
        }
    },

    /** private: method[onScriptLoad]
     *  Called when all resources required by this plugin type have loaded.
     */
    loadScript: function(options) {

        var params = {
            autoload: Ext.encode({
                modules: [{
                    name: "maps",
                    version: 3.7,
                    nocss: "true",
                    callback: "gxp.plugins.GoogleSource.loader.onScriptLoad",
                    other_params: options.otherParams
                }]
            })
        };

        var script = document.createElement("script");
        script.src = window.location.protocol  + "//www.google.com/jsapi?" + Ext.urlEncode(params);

        // cancel loading if monitor is not ready within timeout
        var errback = options.errback || Ext.emptyFn;
        var timeout = options.timeout || gxp.plugins.GoogleSource.prototype.timeout;
        window.setTimeout((function() {
            if (!gxp.plugins.GoogleSource.loader.ready) {
                this.loading = false;
                this.ready = false;
                document.getElementsByTagName("head")[0].removeChild(script);
                errback.call(options.scope);
                this.fireEvent("failure");
                this.purgeListeners();
            }
        }).createDelegate(this), timeout);

        // register callback for ready
        this.on({
            ready: options.callback,
            scope: options.scope
        });

        this.loading = true;

        // The google loader accesses document.body, so we don't add the loader
        // script before the document is ready.
        function append() {
            document.getElementsByTagName("head")[0].appendChild(script);
        }
        if (document.body) {
            append();
        } else {
            Ext.onReady(append);
        }

    }

}))();

Ext.preg(gxp.plugins.GoogleSource.prototype.ptype, gxp.plugins.GoogleSource);
