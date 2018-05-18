/**
 * Copyright (c) 2008-2011 The Open Planning Project
 *
 * Published under the BSD license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = CoordinateTool
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp");

/*
 Create an OpenLayers control to handle right-clicks
 */
OpenLayers.Control.RightClick = OpenLayers.Class(OpenLayers.Control, {

    defaultHandlerOptions: {
        'single': true,
        'double': true,
        'pixelTolerance': 0,
        'stopSingle': false,
        'stopDouble': false
    },
    handleRightClicks:true,
    initialize: function(options) {
        this.handlerOptions = OpenLayers.Util.extend(
            {}, this.defaultHandlerOptions
        );
        OpenLayers.Control.prototype.initialize.apply(
            this, arguments
        );
        this.handler = new OpenLayers.Handler.Click(
            this, this.eventMethods, this.handlerOptions
        );
    },
    CLASS_NAME: "OpenLayers.Control.RightClick"

});

/** api: constructor
 *  .. class:: CoordinateTool(config)
 *
 *    This plugins provides an action which, when active, will display the
 *    coordinates at whatever point the user right-clicks on the map. The output
 *    will be displayed in a popup.
 */
gxp.plugins.CoordinateTool = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = geo_getfeatureinfo */
    ptype: "gxp_coordinatetool",

    /** api: config[outputTarget]
     *  ``String`` Popups created by this tool are added to the map by default.
     */
    outputTarget: "map",

    title: "Map Coordinates (longitude, latitude)",

    /** api: config[infoActionTip]
     *  ``String``
     *  Text for feature info action tooltip (i18n).
     */
    infoActionTip: "Get coordinates at the mouse position",
    
    coordinatePositionText: "CoordinatePosition",
    
    toolText: null,

    iconCls: "gxp-icon-getfeatureinfo",

    coordWindow: null,

    coordDialog: new gxp.MouseCoordinatesDialog(),

    markers: new OpenLayers.Layer.Markers(this.coordinatePositionText,{displayInLayerSwitcher:false}),

    createMarker: function(e){
        this.markers.clearMarkers();

        var size = new OpenLayers.Size(121,125);
        this.markers.addMarker(new OpenLayers.Marker(new OpenLayers.LonLat(e.lon,e.lat)));
    },


    showCoordinates: function(e) {
        this.target.mapPanel.map.addLayer(this.markers);
        var lonlat = this.target.mapPanel.map.getLonLatFromViewPortPx(e.xy);
        this.createMarker(lonlat);
        lonlat.transform(this.target.mapPanel.map.projection, "EPSG:4326");
        this.coordDialog.setCoordinates(lonlat.lon + ',' + lonlat.lat);
        this.coordWindow.show();

    },

    /** api: method[addActions]
     */
    addActions: function() {

        var tool = this;

        this.coordWindow = new Ext.Window({
            title: this.title,
            layout: "fit",
            width: 300,
            autoHeight: true,
            closeAction: "hide",
            listeners: {
                hide:  function() {tool.target.mapPanel.map.removeLayer(tool.markers);}
            },
            items: [ this.coordDialog ]
        });



        // Add an instance of the Click control that listens to rightclick events:
        var oClick = new OpenLayers.Control.RightClick({eventMethods:{
            'rightclick': function(e) {
                tool.showCoordinates(e);
            }
        }});

        this.target.mapPanel.map.addControl(oClick);
        oClick.activate();

        this.target.mapPanel.getEl().on('contextmenu', function(e) {
            e.preventDefault();
        })


        return;
    }


});

Ext.preg(gxp.plugins.CoordinateTool.prototype.ptype, gxp.plugins.CoordinateTool);