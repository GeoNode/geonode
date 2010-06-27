/**
 * Copyright (c) 2010 OpenPlans
 */

/** api: (define)
 *  module = GeoNode
 *  class = ConfigManager
 *  base_link = `Ext.util.Observable <http://extjs.com/deploy/dev/docs/?class=Ext.util.Observable>`_
 */
Ext.namespace("GeoNode");

/** api: constructor
 *  .. class:: ConfigManager(config)
 *   
 *      Utility class for translating between GeoNode and gxp.Viewer
 *      configruations.
 */
GeoNode.ConfigManager = Ext.extend(Ext.util.Observable, {
    /** api: config[useBackgroundCapabilities]
     *  ``Boolean`` If set to false, no GetCapabilities request will be issued
     *  for background WMS layers. The benefit is shorter loading times for
     *  the application. The downside is that layers won't be meta-tiled, and
     *  the name shown in the layer tree is the WMS layer name instead of the
     *  more verbose title.
     */
    useBackgroundCapabilities: true,
    
    backgroundLayers: null,
    map: null,
    
    /**
     * private: property[haveBackground]
     */
    haveBackground: false,

    // i18n defaults
    backgroundDisabledText: "UT: No background",

    constructor: function(config) {
        this.initialConfig = config;
        Ext.apply(this, this.initialConfig);
        this.map = this.map || {layers: []};
        this.backgroundQueue = [];
    },
    
    getViewerConfig: function() {
        var layers = [{
            source: "any",
            type: "OpenLayers.Layer",
            args: [this.backgroundDisabledText],
            visibility: false,
            fixed: true,
            group: "background"
        }];
        var layer;
        for(var i=0,len=this.map.layers.length; i<len; ++i) {
            layer = this.map.layers[i];
            if (layer.group == "background" && layer.visibility !== false) {
                this.haveBackground = true;
            }
            layers.push(Ext.applyIf({
                source: layer.wms,
                buffer: 0
            }, layer));
        }
        var sources = {
            "any": {
                ptype: "gx_olsource"
            }
        };
        for(var key in this.wms) {
            sources[key] = {
                url: this.wms[key]
            }
        }
        var center = this.map.center && new OpenLayers.LonLat(this.map.center[0],
            this.map.center[1]).transform(
                new OpenLayers.Projection("EPSG:4326"),
                new OpenLayers.Projection(
                    this.map.projection || "EPSG:900913"));
        var map = Ext.applyIf({
            projection: "EPSG:900913",
            units: "m",
            maxResolution: 156543.0339,
            maxExtent: [
                -20037508.34, -20037508.34,
                 20037508.34,  20037508.34
            ],
            center: center && [center.lon, center.lat],
            layers: layers
        }, this.map);
        var config = Ext.applyIf({
            defaultSourceType: "gx_wmssource",
            sources: sources,
            map: map
        }, this.initialConfig);
        
        this.backgroundLayers && this.addBackgroundConfig(config);
        
        return Ext.applyIf(config, this.initialConfig);
    },
    
    addBackgroundConfig: function(config) {
        var bgLayer;
        outer:
        for (var i=0,len=this.backgroundLayers.length; i<len; ++i) {
            bgLayer = this.backgroundLayers[i];
            var sourceId;
            if (bgLayer.service === "wms") {
                var layerName = bgLayer.layers instanceof Array ?
                    bgLayer.layers[0] : bgLayer.layers;
                if (this.useBackgroundCapabilities !== false) {
                    sourceId = bgLayer.url;
                    // see if we have the service url already in one of the
                    // sources from the db, and use it
                    for (var s in config.sources) {
                        if (config.sources[s].url == bgLayer.url) {
                            sourceId = s;
                            break;
                        }
                    }
                                        
                    if (!(sourceId in config.sources)) {
                        config.sources[sourceId] = {
                            url: bgLayer.url
                        }
                    }
                    else {
                        // avoid duplicate layers from shared background config
                        // if we have them pulled in already from the db
                        for (var j = 0, jlen = config.map.layers.length; j < jlen; ++j) {
                            if (layerName == config.map.layers[j].name) {
                                continue outer;
                            }
                        }
                    }
                    config.map.layers.push(Ext.apply({
                        source: sourceId,
                        name: layerName,
                        group: "background",
                        buffer: 0,
                        visibility: !this.haveBackground && i === 0,
                        fixed: true
                    }, bgLayer));
                } else {
                    config.map.layers.push({
                        source: "any",
                        type: "OpenLayers.Layer.WMS",
                        group: "background",
                        visibility: !this.haveBackground && i === 0,
                        fixed: true,
                        args: [layerName, bgLayer.url, {
                            layers: bgLayer.layers,
                            format: bgLayer.format || "image/png",
                            styles: bgLayer.styles,
                            transparent: bgLayer.transparent
                        }, {
                            opacity: bgLayer.opacity,
                            buffer: 0
                        }]
                    });
                }
            } else if (bgLayer.service === "google") {
                config.sources["google"] = {
                    ptype: "gx_googlesource",
                    apiKey: bgLayer.apiKey
                }
                config.map.layers.push(Ext.apply({
                    source: "google",
                    group: "background",
                    apiKey: bgLayer.apiKey,
                    name: bgLayer.layers instanceof Array ?
                        bgLayer.layers[0] : bgLayer.layers,
                    visibility: !this.haveBackground && i === 0,
                    fixed: true
                }, bgLayer));
            }
        } 
    },

    getConfig: function(viewer) {
        var viewerConfig = viewer.getState();
        
        var center = viewerConfig.map.center &&
            new OpenLayers.LonLat(viewerConfig.map.center[0],
            viewerConfig.map.center[1]).transform(
                new OpenLayers.Projection(
                    viewerConfig.map.projection || "EPSG:900913"),
                new OpenLayers.Projection("EPSG:4326"));
        var config = {
            wms: {},
            map: {
                center: center && [center.lon, center.lat],
                zoom: viewerConfig.map.zoom,
                layers: []
            },
            about: Ext.apply({}, viewer.about)
        };

        var layer;
        for(var i=0, len=viewerConfig.map.layers.length; i<len; ++i) {
            layer = viewerConfig.map.layers[i];
            if(layer.group !== "background") {
                config.wms[layer.source] = viewerConfig.sources[layer.source].url;
                config.map.layers.push(Ext.apply(layer, {
                    wms: layer.source
                }));
            }
        };
        
        return config;
    }

});
