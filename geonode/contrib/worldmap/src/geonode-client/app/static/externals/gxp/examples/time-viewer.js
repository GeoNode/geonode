var app,
startTime = OpenLayers.Date.parse('2011-08-18T12:00:00.000Z').toISOString();
Ext.onReady(function() {
    app = new gxp.Viewer({
        proxy: "/openlayers/examples/proxy.cgi?url=",
        portalConfig: {
            layout: "border",
            // by configuring items here, we don't need to configure portalItems
            // and save a wrapping container
            items: ["mymap",{
                // container for the layertree
                id: "west",
                xtype: "container",
                layout: "fit",
                region: "west",
                fbar:[],
                width: 200
            }],
            bbar: {id: "mybbar"}
        },
        
        // configuration of all tool plugins for this application
        tools: [{
            ptype: "gxp_layertree",
            outputConfig: {
                id: "tree",
                border: true,
                tbar: [] // we will add buttons to "tree.bbar" later
            },
            outputTarget: "west"
        }, {
            ptype: "gxp_zoomtoextent",
            actionTarget: "map.tbar"
        }, {
            ptype: "gxp_zoom",
            actionTarget: "map.tbar"
        }, {
            ptype: "gxp_navigationhistory",
            actionTarget: "map.tbar"
        },{
            ptype:'gxp_playback',
            controlOptions:{
                units:OpenLayers.TimeUnit.HOURS,
                step:6
            },
            //playbackMode:'ranged',
            //rangedPlayInterval:18,
            outputConfig: {
                dynamicRange: false
            }
        }],
        
        // layer sources
        defaultSourceType: "gxp_wmssource",
        sources: {
            ol: {
                ptype:'gxp_olsource'
            },
            osm: {
                ptype: "gxp_osmsource"
            }/*,
            mapstory:{
                url:'http://mapstory.demo.opengeo.org:8080/geoserver/wms'
            }*/
        },
        
        // map and layers
        map: {
            id: "mymap", // id needed to reference map in portalConfig above
            title: "Map",
            region: 'center',
            projection: "EPSG:900913",
            units: "m",
            maxResolution: 156543.0339,
            center: [-10764594.758211, 4523072.3184791],
            zoom: 3,
            layers: [{
                source: "osm",
                name: "mapnik",
                group: "background"
            }, {
                source: "ol",
                type: 'OpenLayers.Layer.WMS',
                args: ["Hurrican Irene", "http://mapstory.demo.opengeo.org:8080/geoserver/wms", {
                    layers: "irene_11_pts,irene_11_radii,irene_11_lin",
                    transparent: true,
                    format: 'image/png',
                    srs: 'EPSG:900913',
                    time: startTime
                }, {
                    metadata: {
                        timeInterval: [['2011-08-18T12:00:00.000Z','2011-08-29T00:00:00.000Z','PT6H']]
                    },
                    singleTile: true,
                    ratio: 1,
                    transitionEffect: 'resize',
                    visibility: true
                }],
                selected: true
            }, {
                source: "ol",
                type: 'OpenLayers.Layer.WMS',
                args: ["Nexrad", "http://mesonet.agron.iastate.edu/cgi-bin/wms/nexrad/n0r-t.cgi?", {
                    layers: "nexrad-n0r-wmst",
                    transparent: true,
                    format: 'image/png',
                    time: startTime
                }, {
                    metadata: {
                        timeInterval: [['2011-08-18T12:00:00.000Z','2011-08-29T00:00:00.000Z','PT6H']],
                        allowRange:false
                    },
                    singleTile: true,
                    ratio: 1,
                    transitionEffect: 'resize',
                    visibility: true
                }]
            }],
            items: [{
                xtype: "gx_zoomslider",
                vertical: true,
                height: 100
            }]
        }
    });
});
