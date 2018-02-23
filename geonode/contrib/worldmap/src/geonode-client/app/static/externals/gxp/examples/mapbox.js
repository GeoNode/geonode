var app;
Ext.onReady(function() {
    app = new gxp.Viewer({
        portalConfig: {
            renderTo: document.body,
            layout: "border",
            width: 600,
            height: 400,
            border: false,
            items: [{
                xtype: "panel",
                region: "center",
                border: false,
                layout: "fit",
                items: ["map-viewport"]
            }, {
                id: "tree-container",
                xtype: "container",
                layout: "fit",
                region: "west",
                width: 200
            }]
        },
        
        // configuration of all tool plugins for this application
        tools: [{
            ptype: "gxp_layertree",
            outputConfig: {
                id: "tree",
                border: true,
                tbar: [] // we will add buttons to "tree.bbar" later
            },
            outputTarget: "tree-container"
        }, {
            ptype: "gxp_addlayers",
            actionTarget: "tree.tbar"
        }, {
            ptype: "gxp_removelayer",
            actionTarget: ["tree.tbar", "tree.contextMenu"]
        }, {
            ptype: "gxp_zoomtoextent",
            actionTarget: "map.tbar"
        }, {
            ptype: "gxp_zoom",
            actionTarget: "map.tbar"
        }, {
            ptype: "gxp_navigationhistory",
            actionTarget: "map.tbar"
        }],
        
        // layer sources
        sources: {
            mapbox: {
                ptype: "gxp_mapboxsource"
            },
            mapquest: {
                ptype: "gxp_mapquestsource"
            }
        },
        
        // map and layers
        map: {
            id: "map-viewport", // id needed to reference map in items above
            title: "Map",
            projection: "EPSG:900913",
            units: "m",
            maxResolution: 156543.03390625,
            center: [0, 0],
            zoom: 1,
            layers: [{
                source: "mapbox",
                name: "blue-marble-topo-bathy-jan",
                group: "background"
            }],
            items: [{
                xtype: "gx_zoomslider",
                vertical: true,
                height: 100
            }]
        }
    });
});
