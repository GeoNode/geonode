var app;
Ext.onReady(function() {
    app = new gxp.Viewer({
        proxy: "/geoserver/rest/proxy?url=",
        portalConfig: {
            renderTo: document.body,
            layout: "border",
            width: 650,
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
                items: ["mymap", {title: "Dummy Tab"}]
            }, {
                // container for the FeatureGrid
                id: "south",
                xtype: "container",
                layout: "fit",
                region: "south",
                split: true,
                collapsible: true,
                height: 150
            }, {
                // container for the layer manager etc.
                id: "west",
                region: "west",
                xtype: "gxp_crumbpanel",
                collapsible: true,
                collapseMode: "mini",
                hideCollapseTool: true,
                split: true,
                border: true,
                width: 200
            }],
            bbar: {id: "mybbar"}
        },
        
        // configuration of all tool plugins for this application
        tools: [{
            ptype: "gxp_layermanager",
            outputConfig: {
                id: "tree",
                title: "Layers",
                tbar: []  // we will add buttons to "tree.bbar" later
            },
            outputTarget: "west"
        }, {
            ptype: "gxp_addlayers",
            actionTarget: "tree.tbar",
            outputTarget: "west",
            upload: true
        }, {
            ptype: "gxp_removelayer",
            actionTarget: ["tree.tbar", "tree.contextMenu"]
        }, {
            ptype: "gxp_layerproperties",
            outputTarget: "west",
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
        }, {
            ptype: "gxp_wmsgetfeatureinfo",
            outputConfig: {
                width: 400,
                height: 200
            },
            actionTarget: "map.tbar", // this is the default, could be omitted
            toggleGroup: "layertools"
        }, {
            // shared FeatureManager for feature editing, grid and querying
            ptype: "gxp_featuremanager",
            id: "featuremanager",
            maxFeatures: 20
        }, {
            ptype: "gxp_featureeditor",
            featureManager: "featuremanager",
            autoLoadFeature: true, // no need to "check out" features
            outputConfig: {panIn: false},
            toggleGroup: "layertools"
        }, {
            ptype: "gxp_featuregrid",
            featureManager: "featuremanager",
            outputConfig: {
                id: "featuregrid"
            },
            outputTarget: "south"
        }, {
            ptype: "gxp_queryform",
            featureManager: "featuremanager",
            outputConfig: {
                title: "Query",
                width: 320
            },
            actionTarget: ["featuregrid.bbar", "tree.contextMenu"],
            appendActions: false
        }, {
            // not a useful tool - just a demo for additional items
            actionTarget: "mybbar", // ".bbar" would also work
            actions: [{text: "Click me - I'm a tool on the portal's bbar"}]
        }],
        
        // layer sources
        defaultSourceType: "gxp_wmscsource",
        sources: {
            local: {
                url: "/geoserver/wms",
                version: "1.1.1"
            },
            google: {
                ptype: "gxp_googlesource"
            }
        },
        
        // map and layers
        map: {
            id: "mymap", // id needed to reference map in portalConfig above
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
                title: "States, USA - Population",
                queryable: true,
                selected: true,
                bbox: [-13884991.404203, 2870341.1822503, -7455066.2973878, 6338219.3590349],
                tileSize: [256, 256]
            }],
            items: [{
                xtype: "gx_zoomslider",
                vertical: true,
                height: 100
            }]
        }
    });
});
