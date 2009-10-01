Ext.namespace("GeoExplorer");
GeoExplorer.GoogleEarthPanel = Ext.extend(Ext.Panel, {

    /**
     * Google Earth's horizontal field of view, in radians. (30 degrees)
     * This was not pulled from any documentation; it was chosen simply 
     * by it's nice, even number, as well as its appearance to actually
     * work.
     */
    HORIZONTAL_FIELD_OF_VIEW: (30 * Math.PI) / 180,

    map: null,
    mapPanel: null,
    layers: null,
    earth: null,
    projection: null,
    layerCache: null,

    initComponent: function(){
        GeoExplorer.GoogleEarthPanel.superclass.initComponent.call(this);

        if (!this.map) {
            this.map = this.mapPanel && this.mapPanel.map;
        }

        if (!this.layers) {
            this.layers = this.mapPanel && this.mapPanel.layers;
        }

        this.projection = new OpenLayers.Projection("EPSG:4326");
        
        // Unfortunately, the Google Earth plugin does not like to be hidden.
        // No matter whether you hide it through CSS visibility, CSS offsets,
        // or CSS display = none, the Google Earth plugin will show an error
        // message when it is re-enabled. To counteract this, we delete 
        // the instance and create a new one each time.
        this.on("show", function() {
            this.layerCache = {};
            google.earth.createInstance(this.body.dom, this.onEarthReady.createDelegate(this), function(){});
        }, this);
        
        this.on("hide", function() {
            if (this.earth != null) {
                this.updateMap();
                // Remove the plugin from the dom.
                this.body.child("*").remove();
            }
            this.earth = null;
        }, this);
    },

    onEarthReady: function(object){
        this.earth = object;
        
        // We don't want to fly. Just go to the right spot immediately.
        this.earth.getOptions().setFlyToSpeed(this.earth.SPEED_TELEPORT);
        
        // Set the extent of the earth to be that shown in OpenLayers.
        this.resetCamera();
        this.setExtent(this.map.getExtent());
        
        // Show the navigation control, and make it so it is on the left.
        // Not actually sure how the second to fourth lines make that happen,
        // but hey -- it works. :)
        this.earth.getNavigationControl().setVisibility(this.earth.VISIBILITY_SHOW);
        var screenXY = this.earth.getNavigationControl().getScreenXY();
        screenXY.setXUnits(this.earth.UNITS_PIXELS);
        screenXY.setYUnits(this.earth.UNITS_INSET_PIXELS);
        
        // Show the plugin.
        this.earth.getWindow().setVisibility(true);

        this.layers.each(function(record) {
            this.addLayer(record);
        }, this);

        this.layers.on("remove", this.updateLayers, this);

        this.layers.on("update", this.updateLayers, this);
        
        this.layers.on("add", this.updateLayers, this);
        
        // Set up events. Notice global google namespace.
        // google.earth.addEventListener(this.earth.getView(), 
            // "viewchangeend", 
            // this.updateMap.createDelegate(this));
    },

    updateLayers: function() {
        if (!this.earth) return;

        var features = this.earth.getFeatures();
        var f = features.getFirstChild();

        while (f != null) {
            features.removeChild(f);
            f = features.getFirstChild();
        }

        this.layers.each(function(record) {
            this.addLayer(record);
        }, this);
    },
    
    addLayer: function(layer, order) {
        if (this.earth) {
            var name = layer.get("layer").id;

            if (this.layerCache[name]) {
                var networkLink = this.layerCache[name];
            } else {
                var link = this.earth.createLink('kl_' + name);
                var ows = layer.get("layer").url;
                ows = ows.replace(/\?.*/, '');
                var kmlPath = '/kml?mode=refresh&layers=' + layer.get("layer").params.LAYERS;
                link.setHref(ows + kmlPath);
                var networkLink = this.earth.createNetworkLink('nl_' + name);
                networkLink.setName(name);
                networkLink.set(link, false, false);
                this.layerCache[name] = networkLink;
            }

            networkLink.setVisibility(layer.get("layer").getVisibility());

            if (order !== undefined && 
                order < this.earth.getFeatures().getChildNodes().getLength())
            {
                this.earth.getFeatures().
                    insertBefore(this.earth.getFeatures().getChildNodes().item(order));
            } else { 
                this.earth.getFeatures().appendChild(networkLink);
            }
        }
    },
 
    setExtent: function(extent) {
        var extent = extent.transform(this.map.getProjectionObject(), this.projection);
        var center = extent.getCenterLonLat();
        
        var width = this.getExtentWidth(extent);
        
        // Calculate height of the camera from the ground, in meters.
        var height = width / (2 * Math.tan(this.HORIZONTAL_FIELD_OF_VIEW));
        
        var lookAt = this.earth.getView().copyAsLookAt(this.earth.ALTITUDE_RELATIVE_TO_GROUND);
        lookAt.setLatitude(center.lat);
        lookAt.setLongitude(center.lon);
        lookAt.setRange(height);
        this.earth.getView().setAbstractView(lookAt);
    },
    
    resetCamera: function() {
        var camera = this.earth.getView().copyAsCamera(this.earth.ALTITUDE_RELATIVE_TO_GROUND);
        camera.setRoll(0);
        camera.setHeading(0);
        camera.setTilt(0);
        this.earth.getView().setAbstractView(camera);
    },
    
    
    getExtent: function() {
        var geBounds = this.earth.getView().getViewportGlobeBounds();
        var olBounds = new OpenLayers.Bounds(
            geBounds.getWest(), geBounds.getSouth(), geBounds.getEast(), geBounds.getNorth()
        );
        return olBounds;
    },
    
    updateMap: function() {
        // Get the center of the map from GE. We let GE get the center (as opposed to getting
        // the extent and then finding the center) because it'll find the correct visual
        // center represented by the globe, taking into account spherical calculations.
        var lookAt = this.earth.getView().copyAsLookAt(this.earth.ALTITUDE_RELATIVE_TO_GROUND);
        
        var center = this.reprojectToMap(
            new OpenLayers.LonLat(lookAt.getLongitude(), lookAt.getLatitude())
        );
        
        // Zoom to the closest zoom level for the extent given by GE's getViewPortGlobeBounds().
        // Then recenter based on the visual center shown in GE.
        var geExtent = this.reprojectToMap(this.getExtent());
        this.map.zoomToExtent(geExtent, true);
        this.map.setCenter(center);
        
        // Slight dirty hack --
        
        // GE's getViewPortGlobeBounds() function gives us an extent larger than what OL
        // should show, sometimes with more data. This extent works most of the time when OL
        // tries to find the closest zoom level, but on some edge cases it zooms out 
        // one zoom level too far. To counteract this, we calculate the geodetic width that
        // we expect GE to show (note: this is the opposite of the setExtent() calculations),
        // and then compare that width to that of the current zoom level and one zoom level
        // closer. If the next zoom level shows a geodetic width that's nearer to the width
        // we expect, then we zoom to that zoom level.
        //
        // Big note: This expects a map that has fractional zoom disabled!
        var lookAt = this.earth.getView().copyAsLookAt(this.earth.ALTITUDE_RELATIVE_TO_GROUND);
        var height = lookAt.getRange();
        
        var width = 2 * height * Math.tan(this.HORIZONTAL_FIELD_OF_VIEW);
        
        var nextResolution = this.map.getResolutionForZoom(this.map.getZoom() + 1);
        
        var currentExtent = this.map.getExtent();
        var nextExtent = new OpenLayers.Bounds(
            center.lon - (this.map.getSize().w / 2 * nextResolution),
            center.lat + (this.map.getSize().h / 2 * nextResolution),
            center.lon + (this.map.getSize().w / 2 * nextResolution),
            center.lat - (this.map.getSize().h / 2 * nextResolution)
        );
        
        var currentWidthDiff = Math.abs(this.getExtentWidth(currentExtent) - width);
        var nextWidthDiff = Math.abs(this.getExtentWidth(nextExtent) - width);

        if (nextWidthDiff < currentWidthDiff) {
            this.map.zoomTo(this.map.getZoom() + 1);
        }
    },
    
    getExtentWidth: function(extent) {
        var center = extent.getCenterLonLat();
        
        var middleLeft = new OpenLayers.LonLat(extent.left, center.lat);
        var middleRight = new OpenLayers.LonLat(extent.right, center.lat);
        
        return OpenLayers.Util.distVincenty(middleLeft, middleRight) * 1000;
    },
    
    reprojectToGE: function(data) {
        return data.clone().transform(this.map.getProjectionObject(), this.projection);
    },
    
    reprojectToMap: function(data) {
        return data.clone().transform(this.projection, this.map.getProjectionObject());
    }
});
