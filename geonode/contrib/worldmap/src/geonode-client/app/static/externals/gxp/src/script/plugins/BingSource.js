/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/LayerSource.js
 * @requires OpenLayers/Layer/Bing.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = BingSource
 */

/** api: (extends)
 *  plugins/LayerSource.js
 */
Ext.namespace("gxp.plugins");


OpenLayers.Layer.Bing.prototype.loadMetadata = function() {
    this._callbackId = "_callback_" + this.id.replace(/\./g, "_");
    // link the processMetadata method to the global scope and bind it
    // to this instance
    window[this._callbackId] = OpenLayers.Function.bind(
        OpenLayers.Layer.Bing.processMetadata, this
    );
    var params = OpenLayers.Util.applyDefaults({
        key: this.key,
        jsonp: this._callbackId,
        include: "ImageryProviders"
    }, this.metadataParams);
    var url = window.location.protocol  +
        "//dev.virtualearth.net/REST/v1/Imagery/Metadata/" +
        this.type + "?" + OpenLayers.Util.getParameterString(params);
    var script = document.createElement("script");
    script.type = "text/javascript";
    script.src = url;
    script.id = this._callbackId;
    document.getElementsByTagName("head")[0].appendChild(script);
};


/** api: constructor
 *  .. class:: BingSource(config)
 *
 *    Plugin for using Bing layers with :class:`gxp.Viewer` instances.
 *
 *    Available layer names are "Road", "Aerial" and "AerialWithLabels"
 */
/** api: example
 *  The configuration in the ``sources`` property of the :class:`gxp.Viewer` is
 *  straightforward:
 *
 *  .. code-block:: javascript
 *
 *    "bing": {
 *        ptype: "gxp_bingsource"
 *    }
 *
 *  A typical configuration for a layer from this source (in the ``layers``
 *  array of the viewer's ``map`` config option would look like this:
 *
 *  .. code-block:: javascript
 *
 *    {
 *        source: "bing",
 *        title: "Bing Road Map",
 *        name: "Road"
 *    }
 *
 */
gxp.plugins.BingSource = Ext.extend(gxp.plugins.LayerSource, {
    
    /** api: ptype = gxp_bingsource */
    ptype: "gxp_bingsource",

    /** api: property[store]
     *  ``GeoExt.data.LayerStore``. Will contain records with "Road" and
     *  "Aerial" as name field values.
     */
    
    /** api: config[title]
     *  ``String``
     *  A descriptive title for this layer source (i18n).
     */
    title: "Bing Layers",
    
    /** api: config[roadTitle]
     *  ``String``
     *  A descriptive title for the Road layer (i18n).
     */
    roadTitle: "Bing Roads",

    /** api: config[aerialTitle]
     *  ``String``
     *  A descriptive title for the Aerial layer (i18n).
     */
    aerialTitle: "Bing Aerial",

    /** api: config[labeledAerialTitle]
     *  ``String``
     *  A descriptive title for the AerialWithLabels layer (i18n).
     */
    labeledAerialTitle: "Bing Aerial With Labels",
    
    /** api: config[apiKey]
     *  ``String``
     *  API key generated from http://bingmapsportal.com/ for your domain.
     */
    apiKey: "AqTGBsziZHIJYYxgivLBf0hVdrAk9mWO5cQcb8Yux8sW5M8c8opEC2lZqKR1ZZXf",
    
    /** api: method[createStore]
     *
     *  Creates a store of layer records.  Fires "ready" when store is loaded.
     */
    createStore: function() {
        
        var layers = [
            new OpenLayers.Layer.Bing({
                key: this.apiKey,
                name: this.roadTitle,
                type: "Road",
                buffer: 1,
                transitionEffect: "resize"
            }),
            new OpenLayers.Layer.Bing({
                key: this.apiKey,
                name: this.aerialTitle,
                type: "Aerial",
                buffer: 1,
                transitionEffect: "resize"
            }),
            new OpenLayers.Layer.Bing({
                key: this.apiKey,
                name: this.labeledAerialTitle,
                type: "AerialWithLabels",
                buffer: 1,
                transitionEffect: "resize"
            })
        ];
        
        this.store = new GeoExt.data.LayerStore({
            layers: layers,
            fields: [
                {name: "source", type: "string"},
                {name: "name", type: "string", mapping: "type"},
                {name: "abstract", type: "string", mapping: "attribution"},
                {name: "group", type: "string", defaultValue: "background"},
                {name: "fixed", type: "boolean", defaultValue: true},
                {name: "selected", type: "boolean"}
            ]
        });
        this.store.each(function(l) {
            l.set("group", "background");
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
        var index = this.store.findExact("name", config.name);
        if (index > -1) {

            record = this.store.getAt(index).copy(Ext.data.Record.id({}));
            var layer = record.getLayer().clone();
 
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

            record.data.layer = layer;
            record.commit();
        }
        return record;
    }

});

Ext.preg(gxp.plugins.BingSource.prototype.ptype, gxp.plugins.BingSource);
