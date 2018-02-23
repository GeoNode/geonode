var app;
Ext.onReady(function() {
    app = new gxp.Viewer({
        proxy: "/geoserver/rest/proxy?url=",
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
        defaultSourceType: "gxp_wmssource",
        sources: {
            local: {
                title: "Local GeoServer",
                url: "/geoserver/wms",
                version: "1.1.1"
            },
            suite: {
                title: "Remote GeoServer",
                url: "http://v2.suite.opengeo.org/geoserver/wms",
                version: "1.1.1"
            },
            google: {
                ptype: "gxp_googlesource"
            }
        },
        
        // map and layers
        map: {
            id: "map-viewport", // id needed to reference map in items above
            title: "Map",
            projection: "EPSG:900913",
            units: "m",
            maxResolution: 156543.0339,
            maxExtent: [-20037508.34, -20037508.34, 20037508.34, 20037508.34],
            center: [-10764594.758211, 4523072.3184791],
            zoom: 3,
            layers: [{
                source: "google",
                name: "TERRAIN",
                group: "background"
            }, {
                source: "local",
                name: "usa:states",
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
