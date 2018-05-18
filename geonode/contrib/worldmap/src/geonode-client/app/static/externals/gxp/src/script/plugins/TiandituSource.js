/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/LayerSource.js
 * @requires OpenLayers/Layer/Tianditu/v3.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = TiandituSource
 */

/** api: (extends)
 *  plugins/LayerSource.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: TiandituSource(config)
 *
 *    Plugin for using Tianditu layers with :class:`gxp.Viewer` instances. The
 *    plugin uses the BMaps v3 API and also takes care of loading the
 *    required Tianditu resources.
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
 *    "tianditu": {
 *        ptype: "gxp_tianditu"
 *    }
 *
 *  A typical configuration for a layer from this source (in the ``layers``
 *  array of the viewer's ``map`` config option would look like this:
 *
 *  .. code-block:: javascript
 *
 *    {
 *        source: "tianditu",
 *        name: "TERRAIN"
 *    }
 *
 */
gxp.plugins.TiandituSource = Ext.extend(gxp.plugins.LayerSource, {

    /** api: ptype = gxp_tianditusource */
    ptype: "gxp_tianditusource",

    /** config: config[timeout]
     *  ``Number``
     *  The time (in milliseconds) to wait before giving up on the Tianditu Maps
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
    title: "Tianditu Layers",
    tiandituroadAbstract: "Show tiandituRoad",
    tiandituimageAbstract: "Show tiandituImage",
    tiandituterrainAbstract: "Show tiandituTerrain",
    tiandituannotationAbstract: "Show tiandituAnnotation",
    tiandituroadTitle: "Tianditu Road",
    tiandituimageTitle: "Tianditu Image",
    tiandituterrainTitle: "Tianditu Terrain",
    tiandituannotationTitle: "Tianditu Annotation",
    tiandituroadURL: "http://t4.tianditu.com/DataServer?T=vec_w&X=${x}&Y=${y}&L=${z}",
    tiandituimageURL: "http://t4.tianditu.com/DataServer?T=img_w&X=${x}&Y=${y}&L=${z}",
    tiandituterrainURL: "http://t4.tianditu.com/DataServer?T=ter_w&X=${x}&Y=${y}&L=${z}",
    tiandituannotationURL: "http://t4.tianditu.com/DataServer?T=cia_w&X=${x}&Y=${y}&L=${z}",
    /** api: config[otherParams]
     *  ``String``
     *  Additional parameters to be sent to Tianditu,
     *  default is "sensore=false"
     */
    otherParams: "sensor=false",

    constructor: function(config) {
        this.config = config;
        gxp.plugins.TiandituSource.superclass.constructor.apply(this, arguments);
    },

    /** api: method[createStore]
     *
     *  Creates a store of layer records.  Fires "ready" when store is loaded.
     */

    createStore: function() {
        var mapTypes = {
            "TIANDITUROAD": {"abstract": this.tiandituroadAbstract, "title": this.tiandituroadTitle,
                "url":this.tiandituroadURL, "isbaselayer":true, "displayswitch":true},
            "TIANDITUIMAGE": {"abstract": this.tiandituimageAbstract, "title": this.tiandituimageTitle,
                "url":this.tiandituimageURL,  "isbaselayer":true, "displayswitch":true},
            "TIANDITUTERRAIN": {"abstract": this.tiandituterrainAbstract, "title": this.tiandituterrainTitle,
                "url":this.tiandituterrainURL,  "isbaselayer":true, "displayswitch":true},
            "TIANDITUANNOTATION": {"abstract": this.tiandituannotationAbstract, "title": this.tiandituannotationTitle,
                "url":this.tiandituannotationURL, "isbaselayer":false, "displayswitch":false}
        };

        var layers = [];
        var name, mapType;
        for (name in mapTypes) {
            layers.push(new OpenLayers.Layer.XYZ(
                mapTypes[name]["title"],
                [
                    mapTypes[name]["url"],
                    mapTypes[name]["url"],
                    mapTypes[name]["url"],
                    mapTypes[name]["url"],
                    mapTypes[name]["url"],
                    mapTypes[name]["url"],
                    mapTypes[name]["url"],
                    mapTypes[name]["url"]
                ],
                {
                    mapType: name,
                    isBaseLayer: mapTypes[name]["isbaselayer"]
                    //visibility: true,
                    //displayInLayerSwitcher: mapTypes[name]["displayswitch"]
                }
            ));
        }
        this.store = new GeoExt.data.LayerStore({
            layers: layers,
            fields: [
                {name: "source", type: "string"},
                {name: "name", type: "string", mapping: "mapType"},
                {name: "abstract", type: "string"},
                {name: "group", type: "string", defaultValue: "background"},
                {name: "fixed", type: "boolean", defaultValue: true},
                {name: "selected", type: "boolean"}
            ]
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

Ext.preg(gxp.plugins.TiandituSource.prototype.ptype, gxp.plugins.TiandituSource);
