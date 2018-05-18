/**
 * Copyright (c) 2008-2011 The Open Planning Project
 *
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires util.js
 * @requires plugins/LayerSource.js
 * @requires OpenLayers/Layer/WMS.js
 * @requires OpenLayers/Format/WMSCapabilities/v1_1_0.js
 * @requires OpenLayers/Format/WMSCapabilities/v1_1_1.js
 * @requires OpenLayers/Format/WMSCapabilities/v1_3_0.js
 * @requires OpenLayers/Protocol/WFS/v1_1_0.js
 * @requires GeoExt/data/WMSCapabilitiesReader.js
 * @requires GeoExt/data/WMSCapabilitiesStore.js
 * @requires GeoExt/data/WMSDescribeLayerStore.js
 * @requires GeoExt/data/AttributeReader.js
 * @requires GeoExt/data/AttributeStore.js
 */

/**
 * The WMSCapabilities and WFSDescribeFeatureType formats parse the document and
 * pass the raw data to the WMSCapabilitiesReader/AttributeReader.  There,
 * records are created from layer data.  The rest of the data is lost.  It
 * makes sense to store this raw data somewhere - either on the OpenLayers
 * format or the GeoExt reader.  Until there is a better solution, we'll
 * override the reader's readRecords method  here so that we can have access to
 * the raw data later.
 *
 * The purpose of all of this is to get the service title, feature type and
 * namespace later.
 * TODO: push this to OpenLayers or GeoExt
 */
(function() {
    function keepRaw(data) {
        var format = this.meta.format;
        if (typeof data === "string" || data.nodeType) {
            data = format.read(data);
            // cache the data for the single read that readRecord does
            var origRead = format.read;
            format.read = function() {
                format.read = origRead;
                return data;
            };
        }
        // here is the new part
        this.raw = data;
    }
    Ext.intercept(GeoExt.data.WMSCapabilitiesReader.prototype, "readRecords", keepRaw);
    GeoExt.data.AttributeReader &&
    Ext.intercept(GeoExt.data.AttributeReader.prototype, "readRecords", keepRaw);
})();

/** api: (define)
 *  module = gxp.plugins
 *  class = WMSSource
 */

/** api: (extends)
 *  plugins/LayerSource.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: WMSSource(config)
 *
 *    Plugin for using WMS layers with :class:`gxp.Viewer` instances. The
 *    plugin issues a GetCapabilities request to create a store of the WMS's
 *    layers.
 */
/** api: example
 *  Configuration in the  :class:`gxp.Viewer`:
 *
 *  .. code-block:: javascript
 *
 *    defaultSourceType: "gxp_wmssource",
 *    sources: {
 *        "opengeo": {
 *            url: "http://suite.opengeo.org/geoserver/wms"
 *        }
 *    }
 *
 *  A typical configuration for a layer from this source (in the ``layers``
 *  array of the viewer's ``map`` config option would look like this:
 *
 *  .. code-block:: javascript
 *
 *    {
 *        source: "opengeo",
 *        name: "world",
 *        group: "background"
 *    }
 *
 *  For initial programmatic layer configurations, to leverage lazy loading of
 *  the Capabilities document, it is recommended to configure layers with the
 *  fields listed in :obj:`requiredProperties`.
 */
gxp.plugins.WMSSource = Ext.extend(gxp.plugins.LayerSource, {

    /** api: ptype = gxp_wmssource */
    ptype: "gxp_wmssource",

    /** api: config[url]
     *  ``String`` WMS service URL for this source
     */

    /** private: config[restUrl]
     *  ``String`` Optional URL for rest configuration endpoint.  Note that this
     *  property is being added for a specific GeoNode case and it may be
     *  removed if an alternate solution is chosen (like a specific
     *  GeoNodeSource).  This is used where the rest config endpoint cannot
     *  be derived from the source url (e.g. source url "/geoserver" and rest
     *  config url "/other_rest_proxy").
     */

    /** api: config[baseParams]
     *  ``Object`` Base parameters to use on the WMS GetCapabilities
     *  request.
     */
    baseParams: null,

    /** private: property[format]
     *  ``OpenLayers.Format`` Optional custom format to use on the
     *  WMSCapabilitiesStore store instead of the default.
     */
    format: null,

    /** private: property[describeLayerStore]
     *  ``GeoExt.data.WMSDescribeLayerStore`` additional store of layer
     *  descriptions. Will only be available when the source is configured
     *  with ``describeLayers`` set to true.
     */
    describeLayerStore: null,

    /** private: property[describedLayers]
     */
    describedLayers: null,

    /** private: property[schemaCache]
     */
    schemaCache: null,

    /** private: property[ready]
     *  ``Boolean``
     */
    ready: false,

    /** api: config[version]
     *  ``String``
     *  If specified, the version string will be included in WMS GetCapabilities
     *  requests.  By default, no version is set.
     */

    /** api: config[requiredProperties]
     *  ``Array(String)`` List of config properties that are required for each
     *  layer from this source to allow lazy loading, in addition to ``name``.
     *  Default is ``["title", "bbox"]``. When the source loads layers from a
     *  WMS that does not provide layers in all projections, ``srs`` should be
     *  included in this list. Fallback values are available for ``title`` (the
     *  WMS layer name), ``bbox`` (the map's ``maxExtent`` as array), and
     *  ``srs`` (the map's ``projection``, e.g. "EPSG:4326").
     */

    /** api: property[requiredProperties]
     *  ``Array(String)`` List of config properties that are required for a
     *  complete layer configuration, in addition to ``name``.
     */
    requiredProperties: ["title", "bbox"],

    /** private: method[constructor]
     */
    constructor: function(config) {
        // deal with deprecated forceLazy config option
        //TODO remove this before we cut a release
        if (config && config.forceLazy === true) {
            config.requiredProperties = [];
            delete config.forceLazy;
            if (window.console) {
                console.warn("Deprecated config option 'forceLazy: true' for layer source '" +
                    config.id + "'. Use 'requiredProperties: []' instead.");
            }
        }
        gxp.plugins.WMSSource.superclass.constructor.apply(this, arguments);
        if (!this.format) {
            this.format = new OpenLayers.Format.WMSCapabilities({keepData: true});
        }
    },

    /** api: method[init]
     *  :arg target: ``Object`` The object initializing this plugin.
     */
    init: function(target) {
        gxp.plugins.WMSSource.superclass.init.apply(this, arguments);
        this.target.on("authorizationchange", this.onAuthorizationChange, this);
    },

    /** private: method[onAuthorizationChange]
     *  Reload the store when the authorization changes.
     */
    onAuthorizationChange: function() {
        if (this.store && this.store.url.charAt(0) === "/") {
            this.store.reload();
        }
    },

    /** private: method[destroy]
     */
    destroy: function() {
        this.target.un("authorizationchange", this.onAuthorizationChange, this);
        gxp.plugins.WMSSource.superclass.destroy.apply(this, arguments);
    },

    /** private: method[isLazy]
     *  :returns: ``Boolean``
     *
     *  The store for a lazy source will not be loaded upon creation.  A source
     *  determines whether or not it is lazy given the configured layers for
     *  the target.  If the layer configs have all the information needed to
     *  construct layer records, the source can be lazy.
     */
    isLazy: function() {
        var lazy = true;
        var sourceFound = false;
        var mapConfig = this.target.initialConfig.map;
        if (mapConfig && mapConfig.layers) {
            var layerConfig;
            for (var i=0, ii=mapConfig.layers.length; i<ii; ++i) {
                layerConfig = mapConfig.layers[i];
                if (layerConfig.source === this.id) {
                    sourceFound = true;
                    lazy = this.layerConfigComplete(layerConfig);
                    if (lazy === false) {
                        break;
                    }
                }
            }
        }
        return (lazy && sourceFound);
    },

    /** private: method[layerConfigComplete]
     *  :returns: ``Boolean``
     *
     *  A layer configuration is considered complete if it has a title and a
     *  bbox.
     */
    layerConfigComplete: function(config) {
        var lazy = true;
        if (!Ext.isObject(config.capability)) {
            var props = this.requiredProperties;
            for (var i=props.length-1; i>=0; --i) {
                lazy = !!config[props[i]];
                if (lazy === false) {
                    break;
                }
            }
        }
        return lazy;
    },

    /** api: method[createStore]
     *
     *  Creates a store of layer records.  Fires "ready" when store is loaded.
     */
    createStore: function() {
        var baseParams = this.baseParams || {
            SERVICE: "WMS",
            REQUEST: "GetCapabilities"
        };
        if (this.version) {
            baseParams.VERSION = this.version;
        }

        var lazy = this.isLazy();

        this.store = new GeoExt.data.WMSCapabilitiesStore({
            // Since we want our parameters (e.g. VERSION) to override any in the
            // given URL, we need to remove corresponding paramters from the
            // provided URL.  Simply setting baseParams on the store is also not
            // enough because Ext just tacks these parameters on to the URL - so
            // we get requests like ?Request=GetCapabilities&REQUEST=GetCapabilities
            // (assuming the user provides a URL with a Request parameter in it).
            url: this.trimUrl(this.url, baseParams),
            baseParams: baseParams,
            format: this.format,
            autoLoad: !lazy,
            layerParams: {exceptions: null},
            listeners: {
                load: function() {
                    // The load event is fired even if a bogus capabilities doc
                    // is read (http://trac.geoext.org/ticket/295).
                    // Until this changes, we duck type a bad capabilities
                    // object and fire failure if found.
                    if (!this.store.reader.raw || !this.store.reader.raw.service) {
                        this.fireEvent("failure", this, "Invalid capabilities document.");
                    } else {
                        if (!this.title) {
                            this.title = this.store.reader.raw.service.title;
                        }
                        if (!this.ready) {
                            this.ready = true;
                            this.fireEvent("ready", this);
                        } else {
                            this.lazy = false;
                            //TODO Here we could update all records from this
                            // source on the map that were added when the
                            // source was lazy.
                        }
                    }
                    // clean up data stored on format after parsing is complete
                    delete this.format.data;
                },
                exception: function(proxy, type, action, options, response, error) {
                    delete this.store;
                    var msg, details = "";
                    if (type === "response") {
                        if (typeof error == "string") {
                            msg = error;
                        } else {
                            msg = "Invalid response from server.";
                            // special error handling in IE
                            var data = this.format && this.format.data;
                            if (data && data.parseError) {
                                msg += "  " + data.parseError.reason + " - line: " + data.parseError.line;
                            }
                            var status = response.status;
                            if (status >= 200 && status < 300) {
                                // TODO: consider pushing this into GeoExt
                                var report = error && error.arg && error.arg.exceptionReport;
                                details = gxp.util.getOGCExceptionText(report);
                            } else {
                                details = "Status: " + status;
                            }
                        }
                    } else {
                        msg = "Trouble creating layer store from response.";
                        details = "Unable to handle response.";
                    }
                    // TODO: decide on signature for failure listeners
                    this.fireEvent("failure", this, msg, details);
                    // clean up data stored on format after parsing is complete
                    delete this.format.data;
                },
                scope: this
            }
        });
        if (lazy) {
            this.lazy = true;
            //Just assume it's available, run into problems otherwise with ancient WMS's
            // like http://cga-5.hmdc.harvard.edu/tilecache/tiles.py/1.0.0/
            this.ready = true;
            this.fireEvent("ready", this);

            // ping server of lazy source with an incomplete request, to see if
            // it is available
//            Ext.Ajax.request({
//                method: "GET",
//                url: this.url,
//                params: {SERVICE: "WMS"},
//                callback: function(options, success, response) {
//                    var status = response.status;
//                    // responseText should not be empty (OGCException)
//                    if (status >= 200 && status < 500 && response.responseText) {
//                        this.ready = true;
//                        this.fireEvent("ready", this);
//                    } else {
//                        this.fireEvent("failure", this,
//                            "Layer source not available.",
//                            "Unable to contact WMS service."
//                        );
//                    }
//                },
//                scope: this
//            });
        }
    },

    /** private: method[trimUrl]
     *  :arg url: ``String``
     *  :arg params: ``Object``
     *
     *  Remove all parameters from the URL's query string that have matching
     *  keys in the provided object.  Keys are compared in a case-insensitive
     *  way.
     */
    trimUrl: function(url, params, respectCase) {
        var urlParams = OpenLayers.Util.getParameters(url);
        params = OpenLayers.Util.upperCaseObject(params);
        var keys = 0;
        for (var key in urlParams) {
            ++keys;
            if (key.toUpperCase() in params) {
                --keys;
                delete urlParams[key];
            }
        }
        return url.split("?").shift() + (keys ?
            "?" + OpenLayers.Util.getParameterString(urlParams) :
            ""
            );
    },

    /** private: method[createLazyLayerRecord]
     *  :arg config: ``Object`` The application config for this layer.
     *  :returns: ``GeoExt.data.LayerRecord``
     *
     *  Create a minimal layer record
     */
    createLazyLayerRecord: function(config) {
        config = Ext.apply({}, config);

        var srs = config.srs || this.target.map.projection;
        config.srs = {};
        config.srs[srs] = true;

        var bbox = config.bbox || this.target.map.maxExtent || OpenLayers.Projection.defaults[srs].maxExtent;
        config.bbox = {};
        config.bbox[srs] = {bbox: bbox};

        var record;
        if (this.store && this.store instanceof GeoExt.data.WMSCapabilitiesStore) {
            record = new this.store.recordType(config);
        } else {
            record = new GeoExt.data.LayerRecord(config);
        }
        record.setLayer(new OpenLayers.Layer.WMS(
            config.title || config.name,
            config.url || this.url, {
                layers: config.name,
                transparent: "transparent" in config ? config.transparent : true,
                cql_filter: config.cql_filter,
                format: config.format
            }, {
                projection: srs
            }
        ));
        if (record)
            record.json = config;
        return record;
    },

    /** api: method[createLayerRecord]
     *  :arg config:  ``Object``  The application config for this layer.
     *  :returns: ``GeoExt.data.LayerRecord`` or null when the source is lazy.
     *
     *  Create a layer record given the config. Applications should check that
     *  the source is not :obj:`lazy`` or that the ``config`` is complete (i.e.
     *  configured with all fields listed in :obj:`requiredProperties` before
     *  using this method. Otherwise, it is recommended to use the asynchronous
     *  :meth:`gxp.Viewer.createLayerRecord` method on the target viewer
     *  instead, which will load the source's store to complete the
     *  configuration if necessary.
     */
    createLayerRecord: function(config) {
        var record, original;
        var index = this.store.findExact("name", config.name);
        if (index > -1) {
            original = this.store.getAt(index);
        } else if (Ext.isObject(config.capability)) {
            original = this.store.reader.readRecords({capability: {
                request: {getmap: {href: this.url || this.store.url}},
                layers: [config.capability]}
            }).records[0];
        } else if (this.layerConfigComplete(config)) {
            original = this.createLazyLayerRecord(config);
        }
        if (original) {

            var layer = original.getLayer().clone();

            //Update the source url if different from the layer url
            if (layer.url !== this.store.url)
            	this.store.url = this.url = this.trimUrl(layer.url);
            	
            /**
             * TODO: The WMSCapabilitiesReader should allow for creation
             * of layers in different SRS.
             */
            var projection = this.getMapProjection();

            // If the layer is not available in the map projection, find a
            // compatible projection that equals the map projection. This helps
            // us in dealing with the different EPSG codes for web mercator.
            var layerProjection = this.getProjection(original);

            var projCode = (layerProjection || projection).getCode(),
                bbox = original.get("bbox"), maxExtent;
            if (bbox && bbox[projCode]){
                layer.addOptions({projection: layerProjection});
                maxExtent = OpenLayers.Bounds.fromArray(bbox[projCode].bbox, layer.reverseAxisOrder());
            } else {
                var llbbox = original.get("llbbox");
                if (llbbox) {
                    var extent = OpenLayers.Bounds.fromArray(llbbox).transform("EPSG:4326", projection);
                    // make sure maxExtent is valid (transform does not succeed for all llbbox)
                    if ((1 / extent.getHeight() > 0) && (1 / extent.getWidth() > 0)) {
                        // maxExtent has infinite or non-numeric width or height
                        // in this case, the map maxExtent must be specified in the config
                        maxExtent = extent;
                    }
                }
            }

            // update params from config
            layer.mergeNewParams({
                STYLES: config.styles,
                FORMAT: config.format,
                TRANSPARENT: config.transparent,
                CQL_FILTER: config.cql_filter
            });
            
            var singleTile = false;
            if ("tiled" in config) {
                singleTile = !config.tiled;
            } else {
                // for now, if layer has a time dimension, use single tile
                if (original.data.dimensions && original.data.dimensions.time) {
                    singleTile = true;
                }
            }

            layer.setName(config.title || layer.name);
            layer.addOptions({
                attribution: layer.attribution,
                maxExtent: maxExtent,
                restrictedExtent: maxExtent,
                singleTile: singleTile,
                ratio: config.ratio || 1,
                visibility: ("visibility" in config) ? config.visibility : true,
                opacity: ("opacity" in config) ? config.opacity : 1,
                buffer: ("buffer" in config) ? config.buffer : 1,
                dimensions: original.data.dimensions,
                transitionEffect: singleTile ? 'resize' : null,
                minScale: config.minscale,
                maxScale: config.maxscale
            });
            
            // data for the new record
            var data = Ext.applyIf({
                title: layer.name,
                group: config.group,
                infoFormat: config.infoFormat,
                getFeatureInfo:  config.getFeatureInfo,
                source: config.source,
                properties: "gxp_wmslayerpanel",
                fixed: config.fixed,
                selected: "selected" in config ? config.selected : false,
                restUrl: this.restUrl,
                layer: layer
            }, original.data);

            // add additional fields
            var fields = [
                {name: "source", type: "string"},
                {name: "group", type: "string"},
                {name: "properties", type: "string"},
                {name: "fixed", type: "boolean"},
                {name: "selected", type: "boolean"},
                {name: "restUrl", type: "string"},
                {name: "infoFormat", type: "string"},
                {name: "getFeatureInfo"}
            ];
            original.fields.each(function(field) {
                fields.push(field);
            });

            var Record = GeoExt.data.LayerRecord.create(fields);
            record = new Record(data, layer.id);
            record.json = config;

        } else {
            if (window.console && this.store.getCount() > 0) {
                console.warn("Could not create layer record for layer '" + config.name + "'. Check if the layer is found in the WMS GetCapabilities response.");
            }
        }
        return record;
    },

    /** api: method[getProjection]
     *  :arg layerRecord: ``GeoExt.data.LayerRecord`` a record from this
     *      source's store
     *  :returns: ``OpenLayers.Projection`` A suitable projection for the
     *      ``layerRecord``. If the layer is available in the map projection,
     *      the map projection will be returned. Otherwise an equal projection,
     *      or null if none is available.
     *
     *  Get the projection that the source will use for the layer created in
     *  ``createLayerRecord``. If the layer is not available in a projection
     *  that fits the map projection, null will be returned.
     */
    getProjection: function(layerRecord) {
        var projection = this.getMapProjection();
        var compatibleProjection = projection;
        var availableSRS = layerRecord.get("srs");
        if (!availableSRS[projection.getCode()]) {
            compatibleProjection = null;
            var p, srs;
            for (srs in availableSRS) {
                if ((p=new OpenLayers.Projection(srs)).equals(projection)) {
                    compatibleProjection = p;
                    break;
                }
            }
        }
        return compatibleProjection;
    },

    /** private: method[initDescribeLayerStore]
     *  creates a WMSDescribeLayer store for layer descriptions of all layers
     *  created from this source.
     */
    initDescribeLayerStore: function() {
        var raw = this.store.reader.raw;
        if (this.lazy) {
            // When lazy, we assume that the server supports a DescribeLayer
            // request at the layer's url.
            raw = {
                capability: {
                    request: {
                        describelayer: {href: this.url}
                    }
                },
                version: this.version || "1.1.1"
            };
        }
        var req = raw.capability.request.describelayer;
        if (req) {
            var version = raw.version;
            if (parseFloat(version) > 1.1) {
                //TODO don't force 1.1.1, fall back instead
                version = "1.1.1";
            }
            var params = {
                SERVICE: "WMS",
                VERSION: version,
                REQUEST: "DescribeLayer"
            };
            this.describeLayerStore = new GeoExt.data.WMSDescribeLayerStore({
                url: this.trimUrl(req.href, params),
                baseParams: params
            });
        }
    },

    /** api: method[describeLayer]
     *  :arg rec: ``GeoExt.data.LayerRecord`` the layer to issue a WMS
     *      DescribeLayer request for
     *  :arg callback: ``Function`` Callback function. Will be called with
     *      an ``Ext.data.Record`` from a ``GeoExt.data.DescribeLayerStore``
     *      as first argument, or false if the WMS does not support
     *      DescribeLayer.
     *  :arg scope: ``Object`` Optional scope for the callback.
     *
     *  Get a DescribeLayer response from this source's WMS.
     */
    describeLayer: function(rec, callback, scope) {
        if (!this.describeLayerStore) {
            this.initDescribeLayerStore();
        }
        function delayedCallback(arg) {
            window.setTimeout(function() {
                callback.call(scope, arg);
            }, 0);
        }
        if (!this.describeLayerStore) {
            delayedCallback(false);
            return;
        }
        if (!this.describedLayers) {
            this.describedLayers = {};
        }
        var layerName = rec.getLayer().params.LAYERS;
        var cb = function() {
            var recs = Ext.isArray(arguments[1]) ? arguments[1] : arguments[0];
            var rec, name;
            for (var i=recs.length-1; i>=0; i--) {
                rec = recs[i];
                name = rec.get("layerName");
                if (name == layerName) {
                    this.describeLayerStore.un("load", arguments.callee, this);
                    this.describedLayers[name] = true;
                    callback.call(scope, rec);
                    return;
                } else if (typeof this.describedLayers[name] == "function") {
                    var fn = this.describedLayers[name];
                    this.describeLayerStore.un("load", fn, this);
                    fn.apply(this, arguments);
                }
            }
            // something went wrong (e.g. GeoServer does not return a valid
            // DescribeFeatureType document for group layers)
            delete describedLayers[layerName];
            callback.call(scope, false);
        };
        var describedLayers = this.describedLayers;
        var index;
        if (!describedLayers[layerName]) {
            describedLayers[layerName] = cb;
            this.describeLayerStore.load({
                params: {LAYERS: layerName},
                add: true,
                callback: cb,
                scope: this
            });
        } else if ((index = this.describeLayerStore.findExact("layerName", layerName)) == -1) {
            this.describeLayerStore.on("load", cb, this);
        } else {
            delayedCallback(this.describeLayerStore.getAt(index));
        }
    },

    /** private: method[fetchSchema]
     *  :arg url: ``String`` The url fo the WFS endpoint
     *  :arg typeName: ``String`` The typeName to use
     *  :arg callback: ``Function`` Callback function. Will be called with
     *      a ``GeoExt.data.AttributeStore`` containing the schema as first
     *      argument, or false if the WMS does not support DescribeLayer or the
     *      layer is not associated with a WFS feature type.
     *  :arg scope: ``Object`` Optional scope for the callback.
     *
     *  Helper function to fetch the schema for a layer of this source.
     */
    fetchSchema: function(url, typeName, callback, scope) {
        var schema = this.schemaCache[typeName];
        if (schema) {
            if (schema.getCount() == 0) {
                schema.on("load", function() {
                    callback.call(scope, schema);
                }, this, {single: true});
            } else {
                callback.call(scope, schema);
            }
        } else {
            schema = new GeoExt.data.AttributeStore({
                url: url,
                baseParams: {
                    SERVICE: "WFS",
                    //TODO should get version from WFS GetCapabilities
                    VERSION: "1.1.0",
                    REQUEST: "DescribeFeatureType",
                    TYPENAME: typeName
                },
                autoLoad: true,
                listeners: {
                    "load": function() {
                        callback.call(scope, schema);
                    },
                    scope: this
                }
            });
            this.schemaCache[typeName] = schema;
        }
    },

    /** api: method[getSchema]
     *  :arg rec: ``GeoExt.data.LayerRecord`` the WMS layer to issue a WFS
     *      DescribeFeatureType request for
     *  :arg callback: ``Function`` Callback function. Will be called with
     *      a ``GeoExt.data.AttributeStore`` containing the schema as first
     *      argument, or false if the WMS does not support DescribeLayer or the
     *      layer is not associated with a WFS feature type.
     *  :arg scope: ``Object`` Optional scope for the callback.
     *
     *  Gets the schema for a layer of this source, if the layer is a feature
     *  layer.
     */
    getSchema: function(rec, callback, scope) {
        if (!this.schemaCache) {
            this.schemaCache = {};
        }
        this.describeLayer(rec, function(r) {
            if (r && r.get("owsType") == "WFS") {
                var typeName = r.get("typeName");
                var url = r.get("owsURL");
                this.fetchSchema(url, typeName, callback, scope);
            } else if (!r) {
                // When DescribeLayer is not supported, we make the following
                // assumptions:
                // 1. URL of the WFS is the same as the URL of the WMS
                // 2. typeName is the same as the WMS Layer name
                this.fetchSchema(this.url, rec.get('name'), callback, scope);
            } else {
                callback.call(scope, false);
            }
        }, this);
    },

    /** api: method[getWFSProtocol]
     *  :arg record: :class:`GeoExt.data.LayerRecord`
     *  :arg callback: ``Function``
     *  :arg scope: ``Object``
     *  :returns: :class:`OpenLayers.Protocol.WFS`
     *
     *  Creates a WFS protocol for the given WMS layer record.
     */
    getWFSProtocol: function(record, callback, scope) {
        this.getSchema(record, function(schema) {
            var protocol = false;
            if (schema) {
                var geometryName;
                var geomRegex = /gml:((Multi)?(Point|Line|Polygon|Curve|Surface|Geometry)).*/;
                schema.each(function(r) {
                    var match = geomRegex.exec(r.get("type"));
                    if (match) {
                        geometryName = r.get("name");
                    }
                }, this);
                protocol = new OpenLayers.Protocol.WFS({
                    version: "1.1.0",
                    srsName: record.getLayer().projection.getCode(),
                    url: schema.url,
                    featureType: schema.reader.raw.featureTypes[0].typeName,
                    featureNS: schema.reader.raw.targetNamespace,
                    geometryName: geometryName
                });
            }
            callback.call(scope, protocol, schema, record);
        }, this);
    },

    /** api: method[getConfigForRecord]
     *  :arg record: :class:`GeoExt.data.LayerRecord`
     *  :returns: ``Object``
     *
     *  Create a config object that can be used to recreate the given record.
     */
    getConfigForRecord: function(record) {
        var config = Ext.applyIf(
                gxp.plugins.WMSSource.superclass.getConfigForRecord.apply(this, arguments),
                record.json
            ),
            layer = record.getLayer(),
            params = layer.params,
            options = layer.options;
        var name = config.name,
            raw = this.store.reader.raw;
        if (raw) {
            var capLayers = raw.capability.layers;
            for (var i=capLayers.length-1; i>=0; --i) {
                if (capLayers[i].name === name) {
                    config.capability = Ext.apply({}, capLayers[i]);
                    var srs = {};
                    srs[layer.projection.getCode()] = true;
                    // only store the map srs, because this list can be huge
                    config.capability.srs = srs;
                    break;
                }
            }
        }
        if (!config.capability) {
            if (layer.maxExtent) {
                config.bbox = layer.maxExtent.toArray();
            }
            config.srs = layer.projection.getCode();
        }
        return Ext.apply(config, {
            format: params.FORMAT,
            styles: params.STYLES,
            transparent: params.TRANSPARENT,
            cql_filter: params.CQL_FILTER,
            minscale: options.minScale,
            maxscale: options.maxScale,
            infoFormat: record.get("infoFormat")
        });
    },

    /** private: method[getState] */
    getState: function() {
        var state = gxp.plugins.WMSSource.superclass.getState.apply(this, arguments);
        //Force url update in case it was updated from layer url
        Ext.apply(state, {url: this.trimUrl(this.url)});
        return Ext.applyIf(state, {title: this.title});
    },


    /** api: method[getStore]
     *  :returns: ``DataStore``
     *
     *  Return the source datastore
     */
    getStore: function()
    {
        return this.store;
    }

});

Ext.preg(gxp.plugins.WMSSource.prototype.ptype, gxp.plugins.WMSSource);
