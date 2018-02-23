/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/LayerSource.js
 * @requires OpenLayers/Layer/OSM.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = OSMSource
 */

/** api: (extends)
 *  plugins/LayerSource.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: OSMSource(config)
 *
 *    Plugin for using OpenStreetMap layers with :class:`gxp.Viewer` instances.
 *
 *    Available layer names are "mapnik" and "osmarender"
 */
/** api: example
 *  The configuration in the ``sources`` property of the :class:`gxp.Viewer` is
 *  straightforward:
 *
 *  .. code-block:: javascript
 *
 *    "osm": {
 *        ptype: "gxp_osmsource"
 *    }
 *
 *  A typical configuration for a layer from this source (in the ``layers``
 *  array of the viewer's ``map`` config option would look like this:
 *
 *  .. code-block:: javascript
 *
 *    {
 *        source: "osm",
 *        name: "osmarander"
 *    }
 *
 */
gxp.plugins.OSMSource = Ext.extend(gxp.plugins.LayerSource, {
    
    /** api: ptype = gxp_osmsource */
    ptype: "gxp_osmsource",

    /** api: property[store]
     *  ``GeoExt.data.LayerStore``. Will contain records with "mapnik" and
     *  "osmarender" as name field values.
     */
    
    /** api: config[title]
     *  ``String``
     *  A descriptive title for this layer source (i18n).
     */
    title: "OpenStreetMap Layers",

    /** api: config[mapnikAttribution]
     *  ``String``
     *  Attribution string for mapnik generated layer (i18n).
     */
    mapnikAttribution: "Data CC-By-SA by <a href='http://openstreetmap.org/' target='_blank'>OpenStreetMap</a>",

    /** api: config[homeAttribution]
     *  ``String``
     *  Attribution string for osmarender generated layer (i18n).
     */
    osmarenderAttribution: "Data CC-By-SA by <a href='http://openstreetmap.org/' target='_blank'>OpenStreetMap</a>",

    /** api: method[createStore]
     *
     *  Creates a store of layer records.  Fires "ready" when store is loaded.
     */
    createStore: function() {
        
        var options = {
            projection: "EPSG:900913",
            maxExtent: new OpenLayers.Bounds(
                -128 * 156543.0339, -128 * 156543.0339,
                128 * 156543.0339, 128 * 156543.0339
            ),
            maxResolution: 156543.03390625,
            numZoomLevels: 19,
            units: "m",
            buffer: 1,
            transitionEffect: "resize"
        };
        
        var layers = [
            new OpenLayers.Layer.OSM(
                "OpenStreetMap",
                [
                    "http://a.tile.openstreetmap.org/${z}/${x}/${y}.png",
                    "http://b.tile.openstreetmap.org/${z}/${x}/${y}.png",
                    "http://c.tile.openstreetmap.org/${z}/${x}/${y}.png"
                ],
                OpenLayers.Util.applyDefaults({                
                    attribution: this.mapnikAttribution,
                    type: "mapnik"
                }, options)
            )
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

Ext.preg(gxp.plugins.OSMSource.prototype.ptype, gxp.plugins.OSMSource);
