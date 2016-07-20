Ext.namespace("GeoNode");

GeoNode.BoundingBoxWidget = Ext.extend(Ext.util.Observable, {

    /**
     * Property: viewerConfig
     * Options such as background layers configuration to be passed to the
     * gxp.Viewer instance enclosed by this BoundingBoxWidget.
     */
    viewerConfig: null,
    height: 300,
    isEnabled: false,
    useGxpViewer: false,

    gwcBackend: 'http://hh.worldmap.harvard.edu/layer/',
    //gwcBackend: 'http://192.168.33.15:8001/layer/',

    layers: {},

    constructor: function(config, vanillaViewer) {
        Ext.apply(this, config);
        this.doLayout();
    },

    doLayout: function() {

        var self = this;

        var el = Ext.get(this.renderTo);

        var viewerConfig = {
            proxy: this.proxy,
            useCapabilities: false,
            useBackgroundCapabilities: false,
            useToolbar: false,
            useMapOverlay: false,
            portalConfig: {
                collapsed: false,
                border: false,
                height: this.height,
                renderTo: el.query('.bbox-expand')[0]
            },
            listeners: {
                "ready": function() {
                    this._ready = true;
                },
                scope: this,
                showBBox: function(bbox){
                    self.showLayerBBox(bbox);
                },
                hideBBox: function(bbox){
                    self.hideLayerBBox();
                },
                showPreviewLayer: function(typename,layerId){
                    self.showPreviewLayer(typename, layerId);
                },
                hidePreviewLayer: function(){
                    self.hidePreviewLayer();
                },
                showLayer: function(typename, layerId){
                    self.showLayer(typename, layerId);
                },
                hideLayer: function(typename){
                    self.hideLayer(typename);
                },
                zoomToRecord: function(record){
                    self.zoomToRecord(record);
                }
            }
        }

        viewerConfig = Ext.apply(viewerConfig, this.viewerConfig)

        /* Use regular gxp.Viewer if displaying in window on map page, to avoid confusion/conflict with main GeoExplorer instance */
        if (this.useGxpViewer)
        {
            viewerConfig.mapItems = [{
                xtype: "gx_zoomslider",
                vertical: true,
                height: 100
            }];
            this.viewer = new gxp.Viewer(viewerConfig);
        }

        else{
            this.viewer = new GeoExplorer.Viewer(viewerConfig);
        }
    },

    updateBBox: function(bounds) {
        if (bounds && bounds != null)
        {
            var bbmap = this.viewer.mapPanel.map;
            bbmap.zoomToExtent(bounds);
        }
    },

    isActive: function() {
        return true;
    },

    hasConstraint: function() {
        return this.isActive()
    },

    applyConstraint: function(query) {
        /* set parameters in the search query to limit the search to the
         * displayed bounding box.
         */
        if (this.hasConstraint()) {
            var bounds = this.viewer.mapPanel.map.getExtent();
            bounds.transform(
                new OpenLayers.Projection(this.viewerConfig.map.projection),
                new OpenLayers.Projection("EPSG:4326"));
            query.bbox = bounds.toBBOX();
        }
        else if (this._ready) {
            // no constraint, don't include.
            delete query.bbox;
        }
    },

    initFromQuery: function(grid, query) {
        if (query.bbox) {
            var bounds = OpenLayers.Bounds.fromString(query.bbox);
            if (bounds) {
                bounds.transform(
                    new OpenLayers.Projection("EPSG:4326"),
                    new OpenLayers.Projection(this.viewerConfig.map.projection)
                );
                var setMapExtent = function() {
                    var map = this.viewer.mapPanel.map;
                    // when zooming to extent (rather than zoom+center), we
                    // need to wait until the map has its target size
                    map.events.register("moveend", this, function() {
                        map.events.unregister("moveend", this, arguments.callee);
                        map.zoomToExtent(bounds, true);
                    });
                };
                if (this._ready) {
                    setMapExtent.call(this);
                } else {
                    this.viewer.on("ready", setMapExtent, this)
                }
            }
        }
    },

    createBBoxLayer: function() {
        var style_blue = OpenLayers.Util.extend({},
                OpenLayers.Feature.Vector.style['default']);
        /*
         * 4px border, border color: #1D6EEF, background color: #DAEDFF, box
         * opacity: 25%
         */
        style_blue.strokeColor = "#1D6EEF";
        style_blue.fillColor = "#DAEDFF";
        style_blue.fillOpacity = .25;
        style_blue.pointRadius = 10;
        style_blue.strokeWidth = 4;
        style_blue.strokeLinecap = "butt";
        style_blue.zIndex = 999;

        return new OpenLayers.Layer.Vector("layerBBox", {
            style : style_blue,
            displayOutsideMaxExtent : true
        });
    },

    showLayerBBox: function(mapObj) {
        var map = this.viewer.mapPanel.map;
        // add or modify a layer with a vector representing the selected feature
        var featureLayer = map.getLayersByName("layerBBox");
        if (featureLayer.length > 0) {
            featureLayer = featureLayer[0];
            this.hideLayerBBox();
        } else {
            featureLayer = this.createBBoxLayer();
            map.addLayer(featureLayer);
        }
        var bottomLeft = this.WGS84ToMercator(mapObj.west, mapObj.south);
        var topRight = this.WGS84ToMercator(mapObj.east, mapObj.north);

        //if pixel distance b/w topRight and bottomLeft falls below a certain threshold,
        //add a marker(fixed pixel size) in the center, so the user can see where the layer is
        var blPixel = map.getPixelFromLonLat(bottomLeft);
        var trPixel = map.getPixelFromLonLat(topRight);
        var pixelDistance = blPixel.distanceTo(trPixel);
        var threshold = 10;
        var displayMarker = false;

        if (pixelDistance <= threshold){
            displayMarker = true;
        }


        var arrFeatures = [];
        if (bottomLeft.lon > topRight.lon) {
            var dateline = this.WGS84ToMercator(180, 0).lon;
            var geom1 = new OpenLayers.Bounds(
                    bottomLeft.lon, bottomLeft.lat, dateline, topRight.lat)
                    .toGeometry();
            var geom2 = new OpenLayers.Bounds(
                    topRight.lon, topRight.lat, -1 * dateline, bottomLeft.lat)
                    .toGeometry();
            arrFeatures.push(new OpenLayers.Feature.Vector(geom1));
            arrFeatures.push(new OpenLayers.Feature.Vector(geom2));

            if (displayMarker){
                arrFeatures.push(new OpenLayers.Feature.Vector(geom1.getCentroid()));
            }

        } else {
            var geom = new OpenLayers.Bounds(
                    bottomLeft.lon, bottomLeft.lat, topRight.lon, topRight.lat).toGeometry();

            var box = new OpenLayers.Feature.Vector(geom);

            arrFeatures.push(box);

            if (displayMarker){
                arrFeatures.push(new OpenLayers.Feature.Vector(geom.getCentroid()));
            }
        }

        featureLayer.addFeatures(arrFeatures);
        //map.setLayerIndex(featureLayer, (map.layers.length - 1));

        // do a comparison with current map extent
        var extent = this.getVisibleExtent();
        var geodeticExtent = this.getGeodeticExtent();
        var mapTop = extent.top;
        if (geodeticExtent.top > 83) {
            mapTop = 238107694;
        }
        var mapBottom = extent.bottom;
        if (geodeticExtent.bottom < -83) {
            mapBottom = -238107694;
        }
        var mapLeft = extent.left;
        if (geodeticExtent.left < -179) {
            mapLeft = -20037510;
        }
        var mapRight = extent.right;
        if (geodeticExtent.right > 180) {
            mapRight = 20037510;
        }

        var layerTop = topRight.lat;
        var layerBottom = bottomLeft.lat;
        var layerLeft = bottomLeft.lon;
        var layerRight = topRight.lon;



        var showEWArrows = true;
        // don't show arrows for east and west offscreen if multiple "worlds"
        // are on screen
        if (this.hasMultipleWorlds()) {
            showEWArrows = false;
            mapLeft = -20037510;
            mapRight = 20037510;
            extent.left = mapLeft;
            extent.Right = mapRight;
        }

    },

    hideLayerBBox: function() {
        var map = this.viewer.mapPanel.map;
        if (map.getLayersByName("layerBBox").length > 0) {
            var featureLayer = map.getLayersByName("layerBBox")[0];
            featureLayer.removeAllFeatures();
        }
    },

    WGS84ToMercator: function(the_lon, the_lat) {
        // returns -infinity for -90.0 lat; a bug?
        var lat = parseFloat(the_lat);
        var lon = parseFloat(the_lon);
        if (lat >= 90) {
          lat = 89.99;
        }
        if (lat <= -90) {
          lat = -89.99;
        }
        if (lon >= 180) {
          lon = 179.99;
        }
        if (lon <= -180) {
          lon = -179.99;
        }
        // console.log([lon, "tomercator"])
        return OpenLayers.Layer.SphericalMercator.forwardMercator(lon, lat);
    },

    getVisibleExtent: function() {
        var map = this.viewer.mapPanel.map;
        var topLeft = map.getLonLatFromViewPortPx(this.getMapOffset());
        var fullExtent = map.getExtent();
        fullExtent.top = topLeft.lat;
        if (fullExtent.getWidth() >= 40075015.68) {
            fullExtent.left = -20037508.34;
            fullExtent.right = 20037508.34;
        } else {
            fullExtent.left = topLeft.lon;
        }
        return fullExtent;
    },

    getGeodeticExtent: function() {
        var mercatorExtent = this.getVisibleExtent();
        var sphericalMercator = new OpenLayers.Projection('EPSG:3857');
        var geodetic = new OpenLayers.Projection('EPSG:4326');
        return mercatorExtent.transform(sphericalMercator, geodetic);
    },

    getMapOffset: function() {
        var container_id = this.viewer.mapPanel.getId()
        var mapOffset = jQuery("#" + container_id).offset();
        var xOffset = 0;
        var yOffset = mapOffset.top;

        return new OpenLayers.Pixel(xOffset, yOffset);
    },

    hasMultipleWorlds: function() {
        var map = this.viewer.mapPanel.map;
        var exp = map.getZoom() + 8;
        var globalWidth = Math.pow(2, exp);

        var viewPortWidth = map.getSize().w - this.getMapOffset().x;

        if (viewPortWidth > globalWidth) {
            // console.log("has multiple worlds");
            return true;
        } else {
            return false;
        }
    },

    showPreviewLayer: function(typename, layerId){
        var map = this.viewer.mapPanel.map;
        var layer = this.createPreviewLayer(typename, layerId);
        map.addLayer(layer);
    },

    hidePreviewLayer: function(){
        var map = this.viewer.mapPanel.map;
        for(var i=0;i<map.layers.length;i++){
            if(map.layers[i].preview){
                map.removeLayer(map.layers[i]);
            }
        };
    },

    createPreviewLayer: function(typename, layerId){
        var layer = new OpenLayers.Layer.OSM(
            typename,
            this.gwcBackend + layerId + '/map/wmts/' + typename.replace('geonode:', '')  + '/default_grid/${z}/${x}/${y}.png',
            {
                isBaseLayer: false
            }
        );
        layer.preview = true;
        return layer;
    },

    getOrCreateLayer: function(typename, layerId){
        if(!this.layers.hasOwnProperty(typename)){
            var layer = new OpenLayers.Layer.OSM(
                typename,
                this.gwcBackend + layerId + '/map/wmts/' + typename.replace('geonode:', '') + '/default_grid/${z}/${x}/${y}.png',
                {
                    isBaseLayer: false
                }
            );
            this.layers[typename] = layer;
        }
        return this.layers[typename];
    },

    showLayer: function(typename, layerId){
        var map = this.viewer.mapPanel.map;
        var layer = this.getOrCreateLayer(typename, layerId);
        map.addLayer(layer);
    },

    hideLayer: function(typename){
        var map = this.viewer.mapPanel.map;
        var layer = this.getOrCreateLayer(typename);
        map.removeLayer(layer);
    },

    zoomToRecord: function(record){
        var map = this.viewer.mapPanel.map;
        var bounds = new OpenLayers.Bounds(
            [record.get('MinX'),
            record.get('MinY'),
            record.get('MaxX'),
            record.get('MaxY')]
        );
        bounds.transform(
            new OpenLayers.Projection("EPSG:4326"),
            new OpenLayers.Projection(this.viewerConfig.map.projection)
            );
        map.zoomToExtent(bounds, true);
    }
});
