/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

var app1 = new gxp.Viewer({
    portalConfig: {id: "viewer1", xtype: "panel", flex: 1},
    mapItems: [
        {
            xtype: "gx_zoomslider",
            vertical: true,
            height: 100
        }
    ],
    sources: {
        osm: {
            ptype: "gxp_osmsource"
        }
    },
    map: {
        id: "map1",
        region: "center",
        projection: "EPSG:900913",
        units: "m",
        numZoomLevels: 21,
        maxResolution: 156543.03390625,
        maxExtent: [
            -20037508.34, -20037508.34,
            20037508.34, 20037508.34
        ],
        extent: [-13650159, 4534735, -13609227, 4554724],
        layers: [{
            source: "osm",
            name: "mapnik"
        }]
    },
    listeners: {
        portalReady: createViewport
    }
});

var app2 = new gxp.Viewer({
    portalConfig: {id: "viewer2", xtype: "panel", flex: 1},
    portalItems: ["map2", {region: "south", height: 200, title: "A south panel"}],
    mapItems: [
        {
            xtype: "gx_zoomslider",
            vertical: true,
            height: 100
        }
    ],
    sources: {
        osm: {
            ptype: "gxp_osmsource"
        }
    },
    map: {
        id: "map2",
        region: "center",
        projection: "EPSG:900913",
        units: "m",
        numZoomLevels: 21,
        maxResolution: 156543.03390625,
        maxExtent: [
            -20037508.34, -20037508.34,
            20037508.34, 20037508.34
        ],
        extent: [-13650159, 4534735, -13609227, 4554724],
        layers: [{
            source: "osm",
            name: "mapnik"
        }]
    },
    listeners: {
        portalReady: createViewport
    }
});

var portalsReady = 0;
function createViewport() {
    portalsReady++;
    if (portalsReady == 2) {
        new Ext.Viewport({
            layout:'hbox',
            layoutConfig: {
                align : 'stretch',
                pack  : 'start'
            },
            items: ["viewer1", "viewer2"]
        });
    }
}
