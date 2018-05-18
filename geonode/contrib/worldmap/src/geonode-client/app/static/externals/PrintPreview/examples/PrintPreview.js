var mapPanel, printMapPanel, legendPanel;

Ext.onReady(function() {

    var bounds = new OpenLayers.Bounds(
        143.835, -43.648,
        148.479, -39.574
    );
    mapPanel = new GeoExt.MapPanel({
        region: "center",
        map: {
            maxExtent: bounds,
            maxResolution: 0.018140625,
            projection: "EPSG:4326",
            units: 'degrees'
        },
        layers: [
            new OpenLayers.Layer.WMS("Tasmania State Boundaries",
                "http://demo.opengeo.org/geoserver/wms",
                {layers: "topp:tasmania_state_boundaries"},
                {singleTile: true, numZoomLevels: 8}),
            new OpenLayers.Layer.WMS("Tasmania Water Bodies",
                "http://demo.opengeo.org/geoserver/wms",
                {layers: "topp:tasmania_water_bodies", transparent: true},
                {buffer: 0})],
        extent: bounds,
        bbar: [{
            text: "Print...",
            handler: showPrintWindow
        }]
    });

    legendPanel = new GeoExt.LegendPanel({
        width: 200,
        region: "west",
        defaults: {
            style: "padding:5px",
            baseParams: {FORMAT: "image/png"}
        }
    });
    new Ext.Panel({
        layout: "border",
        renderTo: "content",
        width: 800,
        height: 350,
        items: [mapPanel, legendPanel]
    });    
});

function showPrintWindow() {
    var printWindow = new Ext.Window({
        title: "Print",
        modal: true,
        border: false,
        resizable: false,
        width: 360,
        autoHeight: true,
        items: new GeoExt.ux.PrintPreview({
            autoHeight: true,
            printMapPanel: {
                // limit scales to those that can be previewed
                limitScales: true,
                // no zooming on the map
                map: {controls: [
                    new OpenLayers.Control.Navigation({
                        zoomBoxEnabled: false,
                        zoomWheelEnabled: false
                    }),
                    new OpenLayers.Control.PanPanel()
                ]}
            },
            printProvider: {
                // using get for remote service access without same origin
                // restriction. For async requests, we would set method to "POST".
                method: "GET",
                //method: "POST",
                
                // capabilities from script tag in Printing.html.
                capabilities: printCapabilities,
                listeners: {
                    "print": function() {printWindow.close();}
                }
            },
            includeLegend: true,
            mapTitle: "PrintMapPanel Demo",
            sourceMap: mapPanel,
            legend: legendPanel
        })
    }).show().center();
}
