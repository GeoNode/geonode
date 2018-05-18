/**
 * Copyright (c) 2008-2011 The Open Planning Project
 *
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/LayerSource.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = StamenSource
 */

/** api: (extends)
 *  plugins/LayerSource.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: StamenSource(config)
 *
 *    Plugin for using Stamen layers with :class:`gxp.Viewer` instances.
 *
 *    Available layer names:
 *     * toner
 *     * toner-hybrid
 *     * toner-labels
 *     * toner-lines
 *     * toner-background
 *     * toner-lite
 *     * terrain
 *     * terrain-labels
 *     * terrain-lines
 *     * terrain-background
 *     * watercolor
 */
/** api: example
 *  The configuration in the ``sources`` property of the :class:`gxp.Viewer` is
 *  straightforward:
 *
 *  .. code-block:: javascript
 *
 *    "stamen": {
 *        ptype: "gxp_stamensource"
 *    }
 *
 *  A typical configuration for a layer from this source (in the ``layers``
 *  array of the viewer's ``map`` config option would look like this:
 *
 *  .. code-block:: javascript
 *
 *    {
 *        source: "stamen",
 *        name: "watercolor"
 *    }
 *
 */
gxp.plugins.StamenSource = Ext.extend(gxp.plugins.LayerSource, {

    /** api: ptype = gxp_stamensource */
    ptype: "gxp_stamensource",

    /** api: property[store]
     *  ``GeoExt.data.LayerStore``. Will contain records with name field values
     *  matching Stamen layer names.
     */

    /** api: config[title]
     *  ``String``
     *  A descriptive title for this layer source (i18n).
     */
    title: "Stamen Design Layers",

    /** api: config[osmAttribution]
     *  ``String``
     *  Attribution string for OSM generated layer (i18n).
     */
    attribution: "Map tiles by <a href='http://stamen.com'>Stamen Design</a>, under <a href='http://creativecommons.org/licenses/by/3.0'>CC BY 3.0</a>. Data by <a href='http://openstreetmap.org'>OpenStreetMap</a>, under <a href='http://creativecommons.org/licenses/by-sa/3.0'>CC BY SA</a>.",

    /** i18n **/
    tonerTitle: "Toner",
    tonerHybridTitle: "Toner Hybrid",
    tonerLabelsTitle: "Toner Labels",
    tonerLinesTitle: "Toner Lines",
    tonerBackgroundTitle: "Toner Background",
    tonerLiteTitle: "Toner Lite",
    terrainTitle: "Terrain",
    terrainLabelsTitle: "Terrain Labels",
    terrainLinesTitle: "Terrain Lines",
    terrainBackgroundTitle: "Terrain Background",
    watercolorTitle: "Watercolor",

    /** api: method[createStore]
     *
     *  Creates a store of layer records.  Fires "ready" when store is loaded.
     */
    createStore: function() {

        var options = {
            projection: "EPSG:900913",
            numZoomLevels: 20,
            attribution: this.attribution,
            buffer: 0,
            transitionEffect: "resize",
            tileOptions: {crossOriginKeyword: null}
        };

        var configs = [
            {name: "toner", type: "png"},
            {name: "toner-hybrid", type: "png"},
            {name: "toner-labels", type: "png"},
            {name: "toner-lines", type: "png"},
            {name: "toner-background", type: "png"},
            {name: "toner-lite", type: "png"},
            {name: "terrain", type: "png", numZoomLevels: 15, maxResolution: 9783.939619140625},
            {name: "terrain-labels", type: "png", numZoomLevels: 15, maxResolution: 9783.939619140625},
            {name: "terrain-lines", type: "png", numZoomLevels: 15, maxResolution: 9783.939619140625},
            {name: "terrain-background", type: "png", numZoomLevels: 15, maxResolution: 9783.939619140625},
            {name: "watercolor", type: "jpg"}
        ];

        var len = configs.length;
        var layers = new Array(len);
        var config;
        for (var i=0; i<len; ++i) {
            config = configs[i];
            layers[i] = new OpenLayers.Layer.OSM(
                this[OpenLayers.String.camelize(config.name) + "Title"],
                [
                    ["http://tile.stamen.com/", config.name ,"/${z}/${x}/${y}.", config.type].join(""),
                    ["http://a.tile.stamen.com/", config.name ,"/${z}/${x}/${y}.", config.type].join(""),
                    ["http://b.tile.stamen.com/", config.name ,"/${z}/${x}/${y}.", config.type].join(""),
                    ["http://c.tile.stamen.com/", config.name ,"/${z}/${x}/${y}.", config.type].join(""),
                    ["http://d.tile.stamen.com/", config.name ,"/${z}/${x}/${y}.", config.type].join("")
                ],
                OpenLayers.Util.applyDefaults({
                    layername: config.name,
                    numZoomLevels: config.numZoomLevels,
                    maxResolution: config.maxResolution
                }, options)
            );
        }

        this.store = new GeoExt.data.LayerStore({
            layers: layers,
            fields: [
                {name: "source", type: "string"},
                {name: "name", type: "string", mapping: "layername"},
                {name: "abstract", type: "string", mapping: "attribution"},
                {name: "group", type: "string", defaultValue: "background"},
                {name: "fixed", type: "boolean", defaultValue: true},
                {name: "selected", type: "boolean"}
            ]
        });
        this.store.each(function(l) {
            if (l.get("name").search(/labels|lines/i) != -1)
                l.set("group", "");
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

Ext.preg(gxp.plugins.StamenSource.prototype.ptype, gxp.plugins.StamenSource);
