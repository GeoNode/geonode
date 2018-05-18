var app;
Ext.onReady(function() {
    app = new gxp.Viewer({
        proxy: "/geoserver/rest/proxy?url=",
        portalConfig: {
            renderTo: document.body,
            layout: "border",
            height: 465,
            // by configuring items here, we don't need to configure portalItems
            // and save a wrapping container
            items: [{
                // a TabPanel with the map and a dummy tab
                id: "centerpanel",
                xtype: "tabpanel",
                region: "center",
                activeTab: 0, // map needs to be visible on initialization
                border: true,
                items: ["mymap"]
            }]
        },
        
        // configuration of all tool plugins for this application
        tools: [{
            ptype: "gxp_mapproperties",
            outputConfig: {
                title: 'Map properties'
            }
        }],
        // layer sources
        defaultSourceType: "gxp_wmssource",
        sources: {
            suite: {
                url: "http://suite.opengeo.org/geoserver/wms",
                version: "1.1.1"
            }
        },
        
        // map and layers
        map: {
            id: "mymap", // id needed to reference map in portalConfig above
            title: "Map",
            projection: "EPSG:4326",
            layers: [{
                source: "suite",
                name: "world",
                title: "World",
                queryable: true,
                selected: true
            }],
            items: [{
                xtype: "gx_zoomslider",
                vertical: true,
                height: 100
            }]
        }
    });
});
