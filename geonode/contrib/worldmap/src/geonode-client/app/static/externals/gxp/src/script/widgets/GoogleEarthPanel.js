/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp
 *  class = GoogleEarthPanel
 *  base_link = `Ext.Panel <http://extjs.com/deploy/dev/docs/?class=Ext.Panel>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: GoogleEarthPanel(config)
 *   
 *      Create a panel for showing a 3D visualization of
 *      a map with the Google Earth plugin.  
 *      See http://code.google.com/apis/earth/ for plugin api
 *      documentation.
 */
gxp.GoogleEarthPanel = Ext.extend(Ext.Panel, {

    /**
     * Google Earth's horizontal field of view, in radians. (30 degrees)
     * This was not pulled from any documentation; it was chosen simply 
     * by it's nice, even number, as well as its appearance to actually
     * work.
     */
    HORIZONTAL_FIELD_OF_VIEW: (30 * Math.PI) / 180,

    /** api: config[flyToSpeed]
     *  ``Number``
     *  Specifies the speed (0.0 to 5.0) at which the camera moves to the
     *  target extent. Set to null to use the Google Earth default. By default
     *  we show the target extent immediately, without flying to it.
     */

    /** private: property[map]
     *  ``OpenLayers.Map``
     *  The OpenLayers map associated with this panel.  Defaults
     *  to the map of the configured MapPanel
     */
    map: null,

    /** api: config[mapPanel]
     *  ``GeoExt.MapPanel | String``
     *  The map panel associated with this panel.  If a MapPanel instance is 
     *  not provided, a MapPanel id must be provided.
     */
    mapPanel: null,

    /** private: property[layers]
     *  :class:`GeoExt.data.LayerStore`  A store containing
     *  :class:`GeoExt.data.LayerRecord` objects.
     */
    layers: null,

    /** private: property[earth]
     * The Google Earth object.
     */
    earth: null,

    //currently always set to 4326?
    projection: null,

    
    layerCache: null,

    /** private: method[initComponent]
     *  Initializes the Google Earth panel. 
     */
    initComponent: function() {

        this.addEvents(
            /** api: event[beforeadd]
             *  Fires before a layer is added to the 3D view.  If a listener
             *  returns ``false``, the layer will not be added.  Listeners
             *  will be called with a single argument: the layer record.
             */
            "beforeadd",
            /** api: event[pluginfailure]
             *  Fires when there is a failure creating the instance.  Listeners
             *  will receive two arguments: this plugin and the failure code
             *  (see the Google Earth API docs for details on the failure codes).
             */
            "pluginfailure",
            /** api: event[pluginready]
             *  Fires when the instance is ready.  Listeners will receive one
             *  argument: the GEPlugin instance.
             */
            "pluginready"
        );

        gxp.GoogleEarthPanel.superclass.initComponent.call(this);

        var mapPanel = this.mapPanel;
        if (mapPanel && !(mapPanel instanceof GeoExt.MapPanel)) {
            mapPanel = Ext.getCmp(mapPanel);
        }
        if (!mapPanel) {
            throw new Error("Could not get map panel from config: " + this.mapPanel);
        }
        this.map = mapPanel.map;
        this.layers = mapPanel.layers;

        this.projection = new OpenLayers.Projection("EPSG:4326");

        this.on("render", this.onRenderEvent, this);
        this.on("show", this.onShowEvent, this);
        
        this.on("hide", function() {
            if (this.earth != null) {
                this.updateMap();
            }
            // Remove the plugin from the dom.
            this.body.dom.innerHTML = "";
            this.earth = null;
        }, this);
    },

    /** private: method[onEarthReady]
     *  Runs when Google Earth instance is ready.  Adds layer
     *  store handlers. 
     */
    onEarthReady: function(object){
        this.earth = object;
        
        if (this.flyToSpeed === undefined) {
            // We don't want to fly. Just go to the right spot immediately.
            this.earth.getOptions().setFlyToSpeed(this.earth.SPEED_TELEPORT);
        } else if (this.flyToSpeed !== null) {
            this.earth.getOptions().setFlyToSpeed(this.flyToSpeed);
        }
        
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

        this.fireEvent("pluginready", this.earth);

        // Set up events. Notice global google namespace.
        // google.earth.addEventListener(this.earth.getView(), 
            // "viewchangeend", 
            // this.updateMap.createDelegate(this));
    },

    /** private: method[onRenderEvent]
     *  Unfortunately, Ext does not call show() if the component is initally
     *  displayed, so we need to fake it.
     *  We can't call this method onRender because Ext has already stolen
     *  the name for internal use :-(
     */

    onRenderEvent: function() {
        var isCard = this.ownerCt && this.ownerCt.layout instanceof Ext.layout.CardLayout;
        if (!this.hidden && !isCard) {
            this.onShowEvent();
        }
    },

    /** private: method[onShowEvent]
     *  Unfortunately, the Google Earth plugin does not like to be hidden.
     *  No matter whether you hide it through CSS visibility, CSS offsets,
     *  or CSS display = none, the Google Earth plugin will show an error
     *  message when it is re-enabled. To counteract this, we delete
     *  the instance and create a new one each time.
     *  We can't call this method onShow because Ext has already stolen
     *  the name for internal use :-(
     */

    onShowEvent: function() {
        if (this.rendered) {
            this.layerCache = {};
            google.earth.createInstance(
                this.body.dom,
                this.onEarthReady.createDelegate(this),
                (function(code) {
                    this.fireEvent("pluginfailure", this, code);
                }).createDelegate(this)
            );
        }
    },

    /**
     */
    beforeDestroy: function() {
        this.layers.un("remove", this.updateLayers, this);
        this.layers.un("update", this.updateLayers, this);
        this.layers.un("add", this.updateLayers, this);
        gxp.GoogleEarthPanel.superclass.beforeDestroy.call(this);
    },

    /** private: method[updateLayers]
     *  Synchronizes the 3D visualization with the
     *  configured layer store.
     */

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

    /** private: method[addLayer]
     *  Adds a layer to the 3D visualization.
     */
    
    addLayer: function(layer, order) {
        var lyr = layer.getLayer();
        var ows = (lyr && lyr.url);
        if (this.earth && lyr instanceof OpenLayers.Layer.WMS && typeof ows == "string") {
            var add = this.fireEvent("beforeadd", layer);
            if (add !== false) {
                var name = lyr.id;
                var networkLink;
                if (this.layerCache[name]) {
                    networkLink = this.layerCache[name];
                } else {
                    var link = this.earth.createLink('kl_' + name);
                    ows = ows.replace(/\?.*/, '');
                    var params = lyr.params;
                    var kmlPath = '/kml?mode=refresh&layers=' + params.LAYERS +
                        "&styles=" + params.STYLES;
                    link.setHref(ows + kmlPath);
                    networkLink = this.earth.createNetworkLink('nl_' + name);
                    networkLink.setName(name);
                    networkLink.set(link, false, false);
                    this.layerCache[name] = networkLink;
                }

                networkLink.setVisibility(lyr.getVisibility());

                if (order !== undefined && order < this.earth.getFeatures().getChildNodes().getLength()) {
                    this.earth.getFeatures().
                        insertBefore(this.earth.getFeatures().getChildNodes().item(order));
                } else { 
                    this.earth.getFeatures().appendChild(networkLink);
                }
            }
        }
    },

    /** private: method[setExtent]
     *  Sets the view of the 3D visualization to approximate an OpenLayers extent.
     */
    setExtent: function(extent) {
        extent = extent.transform(this.map.getProjectionObject(), this.projection);
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

    /** private: method[getExtent]
     *  Gets an OpenLayers.Bounds that approximates the visable area of
     *  3D visualization.
     */ 
    getExtent: function() {
        var geBounds = this.earth.getView().getViewportGlobeBounds();
        var olBounds = new OpenLayers.Bounds(
            geBounds.getWest(), geBounds.getSouth(), geBounds.getEast(), geBounds.getNorth()
        );
        return olBounds;
    },


    /** private: method[updateMap]
     */
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


    /** private: method[getExentWidth]
     */
    getExtentWidth: function(extent) {
        var center = extent.getCenterLonLat();
        
        var middleLeft = new OpenLayers.LonLat(extent.left, center.lat);
        var middleRight = new OpenLayers.LonLat(extent.right, center.lat);
        
        return OpenLayers.Util.distVincenty(middleLeft, middleRight) * 1000;
    },
    

    /** private: method[reprojectToGE]
     */
    reprojectToGE: function(data) {
        return data.clone().transform(this.map.getProjectionObject(), this.projection);
    },
    

    /** private: method[reprojectToMap]
     */
    reprojectToMap: function(data) {
        return data.clone().transform(this.projection, this.map.getProjectionObject());
    }
});


/** api: xtype = gxp_googleearthpanel */
Ext.reg("gxp_googleearthpanel", gxp.GoogleEarthPanel);
