 /**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[print-preview-osm]
 *  Printing OpenStreetMap
 *  ----------------------------------------
 *  PrintMapPanel with an OSM map.
 */

var mapPanel, printDialog;

Ext.onReady(function() {
    // The PrintProvider that connects us to the print service
    var printProvider = new GeoExt.data.PrintProvider({
        method: "GET", // "POST" recommended for production use
        capabilities: printCapabilities, // provide url instead for lazy loading
        customParams: {
            mapTitle: "GeoExt Printing Demo",
            comment: "This demo shows how to use GeoExt.PrintMapPanel with OSM"
        }
    });
    
    // A MapPanel with a "Print..." button
    mapPanel = new GeoExt.MapPanel({
        renderTo: "content",
        width: 500,
        height: 350,
        map: {
            maxExtent: new OpenLayers.Bounds(
                -128 * 156543.0339,
                -128 * 156543.0339,
                128 * 156543.0339,
                128 * 156543.0339
            ),
            maxResolution: 156543.0339,
            units: "m",
            projection: "EPSG:900913"
        },
        layers: [new OpenLayers.Layer.OSM()],
        /*layers: [new OpenLayers.Layer.WMS("Tasmania State Boundaries",
            "http://demo.opengeo.org/geoserver/wms",
            {layers: "topp:tasmania_state_boundaries"}, {singleTile: true})],*/
        center: [16314984.568391, -5095295.7603428],
        zoom: 6,
        bbar: [{
            text: "Print...",
            handler: function(){
                // A window with the PrintMapPanel, which we can use to adjust
                // the print extent before creating the pdf.
                printDialog = new Ext.Window({
                    title: "Print Preview",
                    width: 350,
                    autoHeight: true,
                    items: [{
                        xtype: "gx_printmappanel",
                        // use only a PanPanel control
                        map: {controls: [new OpenLayers.Control.PanPanel()]},
                        sourceMap: mapPanel,
                        printProvider: printProvider
                    }],
                    bbar: [{
                        text: "Create PDF",
                        handler: function(){ printDialog.items.get(0).print(); }
                    }]
                });
                printDialog.show();
            }
        }]
    });

});