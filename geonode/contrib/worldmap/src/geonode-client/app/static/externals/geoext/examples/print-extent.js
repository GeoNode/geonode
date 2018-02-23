 /**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[print-extent]
 *  Interactive Print Extent
 *  ------------------------
 *  Change print scale, center and rotation with the PrintExtent plugin.
 */

var mapPanel, printProvider;

Ext.onReady(function() {
    // The printProvider that connects us to the print service
    printProvider = new GeoExt.data.PrintProvider({
        method: "GET", // "POST" recommended for production use
        capabilities: printCapabilities, // from the info.json script in the html
        customParams: {
            mapTitle: "Printing Demo",
            comment: "This is a map printed from GeoExt."
        }
    });

    var printExtent = new GeoExt.plugins.PrintExtent({
        printProvider: printProvider
    });

    // The map we want to print, with the PrintExtent added as item.
    mapPanel = new GeoExt.MapPanel({
        renderTo: "content",
        width: 450,
        height: 320,
        layers: [new OpenLayers.Layer.WMS("Tasmania", "http://demo.opengeo.org/geoserver/wms",
            {layers: "topp:tasmania_state_boundaries"}, {singleTile: true})],
        center: [146.56, -41.56],
        zoom: 6,
        plugins: [printExtent],
        bbar: [{
            text: "Create PDF",
            handler: function() {
                // the PrintExtent plugin is the mapPanel's 1st plugin
                mapPanel.plugins[0].print();
            }
        }]
    });
    printExtent.addPage();
});
