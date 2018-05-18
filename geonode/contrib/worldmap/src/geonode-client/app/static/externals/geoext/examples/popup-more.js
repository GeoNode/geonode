/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[popup-more]
 *  Modifying Popups
 *  ----------------
 *  Update a popup with information from multiple locations.
 */

var mapPanel, popup;

Ext.onReady(function() {

    function addToPopup(loc) {

        // create the popup if it doesn't exist
        if (!popup) {
            popup = new GeoExt.Popup({
                title: "Popup",
                width: 200,
                maximizable: true,
                collapsible: true,
                map: mapPanel.map,
                anchored: true,
                listeners: {
                    close: function() {
                        // closing a popup destroys it, but our reference is truthy
                        popup = null;
                    }
                }
            });
        }

        // add some content to the popup (this can be any Ext component)
        popup.add({
            xtype: "box",
            autoEl: {
                html: "You clicked on (" + loc.lon.toFixed(2) + ", " + loc.lat.toFixed(2) + ")"
            }
        });

        // reset the popup's location
        popup.location = loc;
        
        popup.doLayout();

        // since the popup is anchored, calling show will move popup to this location
        popup.show();
    }

    // create Ext window including a map panel
    var mapPanel = new GeoExt.MapPanel({
        title: "Map",
        renderTo: "container",
        width: 650, height: 356,
        layers: [
            new OpenLayers.Layer.WMS(
                "Global Imagery",
                "http://maps.opengeo.org/geowebcache/service/wms",
                {layers: "bluemarble"}
            )
        ],
        center: [0, 0],
        zoom: 2
    });

    var control = new OpenLayers.Control.Click({
        trigger: function(evt) {
            var loc = mapPanel.map.getLonLatFromViewPortPx(evt.xy);
            addToPopup(loc);
        }
    });
    
    mapPanel.map.addControl(control);
    control.activate();

});

// simple control to handle user clicks on the map

OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {                

    defaultHandlerOptions: {
        single: true,
        double: false,
        pixelTolerance: 0,
        stopSingle: true
    },

    initialize: function(options) {

        this.handlerOptions = OpenLayers.Util.extend(
            options && options.handlerOptions || {}, 
            this.defaultHandlerOptions
        );
        OpenLayers.Control.prototype.initialize.apply(
            this, arguments
        ); 
        this.handler = new OpenLayers.Handler.Click(
            this, 
            {
                click: this.trigger
            }, 
            this.handlerOptions
        );
    },
    
    CLASS_NAME: "OpenLayers.Control.Click"

});
