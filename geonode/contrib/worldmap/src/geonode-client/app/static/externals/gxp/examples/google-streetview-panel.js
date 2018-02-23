/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

var Clicker = OpenLayers.Class(OpenLayers.Control, {                

    defaults: {
        pixelTolerance: 1,
        stopSingle: true
    },

    initialize: function(options) {
        this.handlerOptions = OpenLayers.Util.extend(
            {}, this.defaults
        );
        OpenLayers.Control.prototype.initialize.apply(this, arguments); 
        this.handler = new OpenLayers.Handler.Click(
            this, {click: this.trigger}, this.handlerOptions
        );
    }, 

    trigger: function(event) {
        openPopup(this.map.getLonLatFromViewPortPx(event.xy));
    }

});


var geog = new OpenLayers.Projection("EPSG:4326");
var merc = new OpenLayers.Projection("EPSG:900913");

var sf = new OpenLayers.LonLat(-122.45, 37.76).transform(geog, merc);


var mapPanel = new GeoExt.MapPanel({
    title: "Map",
    renderTo: "container",
    height: 600,
    width: 600,
    map: {
        theme: null,
        projection: merc,
        units: "m",
        numZoomLevels: 18,
        maxResolution: 156543.0339,
        maxExtent: new OpenLayers.Bounds(
            -20037508.34, -20037508.34,
            20037508.34, 20037508.34
        ),
        controls: [
            new OpenLayers.Control.Navigation(),
            new Clicker({autoActivate: true})
        ],
        layers: [new OpenLayers.Layer.Google("Streets")]
    },
    center: sf,
    zoom: 12
});

var popup;
function openPopup(location) {
    if (!location) {
        location = mapPanel.map.getCenter();
    }
    if (popup && popup.anc) {
        popup.close();
    }

    popup = new GeoExt.Popup({
        title: "Street View",
        location: location,
        width: 300,
        height: 300,
        collapsible: true,
        map: mapPanel,
        items: [new gxp.GoogleStreetViewPanel()]
    });
    popup.show();
}

openPopup();
