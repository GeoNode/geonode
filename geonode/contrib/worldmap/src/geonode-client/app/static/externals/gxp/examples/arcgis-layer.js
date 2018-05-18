var app;
Ext.onReady(function() {
    app = new gxp.Viewer({
        portalConfig: {
            renderTo: document.body,
            layout: "border",
            border: false,
            width: 600,
            height: 400,
            items: ["mymap", {
                id: "west",
                xtype: "container",
                layout: "fit",
                region: "west",
                width: 180
            }]
        },
        
        // configuration of all tool plugins for this application
        tools: [{
            ptype: "gxp_layertree",
            outputConfig: {
                id: "tree",
                border: false
            },
            outputTarget: "west"
        }],
        
        // layer sources
        sources: {
            ol: {
                ptype: "gxp_olsource"
            }
        },
        
        // map and layers
        map: {
            id: "mymap", // id needed to reference map in portalConfig above
            projection: "EPSG:4326",
            units: "m",
            center: [-114.5, 42.5],
            zoom: 4,
            layers: [{
                source: "ol",
                type: "OpenLayers.Layer.WMS",
                args: [
                    "Natural Earth",
                    "http://demo.opengeo.org/geoserver/wms",
                    {layers: "topp:naturalearth"}
                ],
                visibility: true,
                group: "background"
            }, {
                source: "ol",
                type: "OpenLayers.Layer.ArcGIS93Rest",
                args: [
                    "ArcGIS Server Layer",
                    "http://sampleserver1.arcgisonline.com/ArcGIS/rest/services/Specialty/ESRI_StateCityHighway_USA/MapServer/export", 
                    {layers: "show:0,2", transparent: true}
                ],
                visibility: true
            }],
            items: [{
                xtype: "gx_zoomslider",
                vertical: true,
                height: 100
            }]
        }
    });
});
