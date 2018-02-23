/**
 * Copyright (c) 2008-2011 The Open Planning Project
 *
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/WMSSource.js
 * @requires OpenLayers/Format/WMSCapabilities/v1_1_1_WMSC.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = WMSCSource
 */

/** api: (extends)
 *  plugins/WMSSource.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: WMSCSource(config)
 *
 *    Plugin for using WMS-C layers with :class:`gxp.Viewer` instances. The
 *    plugin issues a GetCapabilities request to create a store of the WMS's
 *    layers. If tilesets are available, it will use them.
 */
/** api: example
 *  Configuration in the  :class:`gxp.Viewer`:
 *
 *  .. code-block:: javascript
 *
 *    defaultSourceType: "gxp_wmscsource",
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
 */
gxp.plugins.WMSCSource = Ext.extend(gxp.plugins.WMSSource, {

    /** api: ptype = gxp_wmscsource */
    ptype: "gxp_wmscsource",

    /** api: config[version]
     *  ``String``
     *  Only WMS 1.1.1 is supported at the moment.
     */
    version: "1.1.1",

    /** api: config[requiredProperties]
     *  ``Array(String)`` List of config properties that are required for each
     *  layer from this source to allow lazy loading. Default is
     *  ``["title", "bbox"]``. When the source loads layers from a WMS-C that
     *  does not use subsets of the default Web Mercator grid, not provide
     *  tiles for all default Web Mercator resolutions, and not use a tileSize
     *  of 256x256 pixels, ``tileOrigin``, ``resolutions`` and ``tileSize``
     *  should be included in this list.
     */

    /** private: method[constructor]
     */
    constructor: function(config) {
        config.baseParams = {
            SERVICE: "WMS",
            REQUEST: "GetCapabilities",
            TILED: true
        };
        if (!config.format) {
            this.format = new OpenLayers.Format.WMSCapabilities({
                keepData: true,
                profile: "WMSC"
            });
        }
        gxp.plugins.WMSCSource.superclass.constructor.apply(this, arguments);
    },

    /** private: method[createLayerRecord] */
    createLayerRecord: function(config) {
        var record = gxp.plugins.WMSCSource.superclass.createLayerRecord.apply(this, arguments);
        if (!record) {
            return;
        }
        var caps, srs;
        if (this.store.reader.raw) {
            caps = this.store.reader.raw.capability;
        }
        var tileSets = (caps && caps.vendorSpecific) ?
            caps.vendorSpecific.tileSets : (config.capability && config.capability.tileSets);
        var layer = record.get("layer");
        if (tileSets) {
            var mapProjection = this.getProjection(record) || this.getMapProjection();
            // look for tileset with same name and equivalent projection
            for (var i=0, len=tileSets.length; i<len; i++) {
                var tileSet = tileSets[i];
                if (tileSet.layers === layer.params.LAYERS) {
                    var tileProjection;
                    for (srs in tileSet.srs) {
                        tileProjection = new OpenLayers.Projection(srs);
                        break;
                    }
                    if (mapProjection.equals(tileProjection)) {
                        var bbox = tileSet.bbox[srs].bbox;
                        layer.projection = tileProjection;
                        layer.addOptions({
                            resolutions: tileSet.resolutions,
                            tileSize: new OpenLayers.Size(tileSet.width, tileSet.height),
                            tileOrigin: new OpenLayers.LonLat(bbox[0], bbox[1])
                        });
                        break;
                    }
                }
            }
        } else if (this.lazy) {
            // lazy loading
            var tileSize = config.tileSize,
                tileOrigin = config.tileOrigin;
            layer.addOptions({
                resolutions: config.resolutions,
                tileSize: tileSize ? new OpenLayers.Size(tileSize[0], tileSize[1]) : undefined,
                tileOrigin: tileOrigin ? OpenLayers.LonLat.fromArray(tileOrigin) : undefined
            });
            if (!tileOrigin) {
                // If tileOrigin was not set, our best bet is to use the map's
                // maxExtent, because GWC's tiling scheme always aligns to the
                // default Web Mercator grid. We don't do this with addOptions
                // because we persist the config from layer.options in
                // getConfigForRecord, and we don't want to persist a guessed
                // configuration.
                var maxExtent;
                if (this.target.map.maxExtent) {
                    maxExtent = this.target.map.maxExtent;
                } else {
                    srs = config.srs || this.target.map.projection;
                    maxExtent = OpenLayers.Projection.defaults[srs].maxExtent;
                }
                if (maxExtent) {
                    layer.tileOrigin = OpenLayers.LonLat.fromArray(maxExtent);
                }
            }
        }
        // unless explicitly configured otherwise, use cached version
        layer.params.TILED = (config.cached !== false) && true;
        return record;
    },

    /** api: method[getConfigForRecord]
     *  :arg record: :class:`GeoExt.data.LayerRecord`
     *  :returns: ``Object``
     *
     *  Create a config object that can be used to recreate the given record.
     */
    getConfigForRecord: function(record) {
        var config = gxp.plugins.WMSCSource.superclass.getConfigForRecord.apply(this, arguments),
            name = config.name,
            tileSetsCap,
            layer = record.getLayer();
        if (config.capability) {
            var capability = this.store.reader.raw.capability;
            var tileSets = capability.vendorSpecific && capability.vendorSpecific.tileSets;
            if (tileSets) {
                for (var i=tileSets.length-1; i>=0; --i) {
                    tileSetsCap = tileSets[i];
                    if (tileSetsCap.layers === name && tileSetsCap.srs[layer.projection]) {
                        config.capability.tileSets = [tileSetsCap];
                        break;
                    }
                }
            }
            if (!config.capability||(config.capability && !config.capability.tileSets)) {
                var tileSize = layer.options.tileSize;
                if (tileSize) {
                    config.tileSize = [tileSize.w, tileSize.h];
                    config.tileOrigin = layer.options.tileOrigin;
                    config.resolutions = layer.options.resolutions;
                }
            }
        }

        if (!(config.capability && config.capability.tileSets)) {
            var tileSize = layer.options.tileSize;
            if (tileSize) {
                config.tileSize = [tileSize.w, tileSize.h];
            }
            config.tileOrigin = layer.options.tileOrigin;
            config.resolutions = layer.options.resolutions;
        }
        return Ext.applyIf(config, {
            // the "tiled" property is already used to indicate singleTile
            // the "cached" property will indicate whether to send the TILED param
            cached: !!layer.params.TILED
        });
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

Ext.preg(gxp.plugins.WMSCSource.prototype.ptype, gxp.plugins.WMSCSource);
