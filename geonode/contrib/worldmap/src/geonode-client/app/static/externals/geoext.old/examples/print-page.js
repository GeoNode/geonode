 /**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[print-page]
 *  Print Your Map
 *  --------------
 *  Print the visible extent of a MapPanel with PrintPage and PrintProvider.
 */

var mapPanel, printPage;

Ext.onReady(function() {
    // The printProvider that connects us to the print service
    var printProvider = new GeoExt.data.PrintProvider({
        method: "GET", // "POST" recommended for production use
        capabilities: printCapabilities, // from the info.json script in the html
        customParams: {
            mapTitle: "Printing Demo",
            comment: "This is a simple map printed from GeoExt."
        }
    });
    // Our print page. Tells the PrintProvider about the scale and center of
    // our page.
    printPage = new GeoExt.data.PrintPage({
        printProvider: printProvider
    });

    // The map we want to print
    mapPanel = new GeoExt.MapPanel({
        region: "center",
        layers: [new OpenLayers.Layer.WMS("Tasmania", "http://demo.opengeo.org/geoserver/wms",
            {layers: "topp:tasmania_state_boundaries"}, {singleTile: true})],
        center: [146.56, -41.56],
        zoom: 7
    });
    // The legend to optionally include on the printout
    var legendPanel = new GeoExt.LegendPanel({
        region: "west",
        width: 150,
        bodyStyle: "padding:5px",
        layerStore: mapPanel.layers
    });
    
    var includeLegend; // controlled by the "Include legend?" checkbox
     
    // The main panel
    new Ext.Panel({
        renderTo: "content",
        layout: "border",
        width: 700,
        height: 420,
        items: [mapPanel, legendPanel],
        bbar: ["->", {
            text: "Print",
            handler: function() {
                // convenient way to fit the print page to the visible map area
                printPage.fit(mapPanel, true);
                // print the page, optionally including the legend
                printProvider.print(mapPanel, printPage, includeLegend && {legend: legendPanel});
            }
        }, {
            xtype: "checkbox",
            boxLabel: "Include legend?",
            handler: function() {includeLegend = this.checked}
        }]
    });
});
