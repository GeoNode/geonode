/**
 * Copyright (c) 2010 OpenPlans
 */

Ext.namespace("GeoNode");

/**
 *
 */
GeoNode.ConfigManager = Ext.extend(Ext.util.Observable, {
    backgroundLayers: null,
    map: null,
    
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
                sourceId = bgLayer.url;
                // see if we have the service url already in one of the
                // sources from the db, and use it
                for (var s in config.sources) {
                    if (config.sources[s].url == bgLayer.url) {
                        sourceId = s;
                        break;
                    }
                }
                
                var layerName = bgLayer.layers instanceof Array ?
                        bgLayer.layers[0] : bgLayer.layers;
                        
                if (!(sourceId in config.sources)) {
                    config.sources[sourceId] = {
                        url: bgLayer.url
                    }
                } else {
                    // avoid duplicate layers from shared background config
                    // if we have them pulled in already from the db
                    for (var j=0,jlen=config.map.layers.length; j<jlen; ++j) {
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
