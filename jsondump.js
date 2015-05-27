{
    "defaultSourceType": "gxp_wmscsource",
    "about": {
        "abstract": "",
        "title": ""
    },
    "map": {
        "layers": [{
            "opacity": 1,
            "group": "background",
            "args": ["No background"],
            "visibility": false,
            "source": "0",
            "fixed": true,
            "type": "OpenLayers.Layer"
        }, {
            "opacity": 1,
            "group": "background",
            "name": "mapnik",
            "visibility": false,
            "source": "1",
            "fixed": true,
            "type": "OpenLayers.Layer.OSM"
        }, {
            "opacity": 1,
            "group": "background",
            "name": "osm",
            "visibility": true,
            "source": "2",
            "fixed": false
        }, {
            "opacity": 1,
            "group": "background",
            "name": "naip",
            "visibility": false,
            "source": "2",
            "fixed": false
        }, {
            "opacity": 1,
            "group": "background",
            "name": "AerialWithLabels",
            "visibility": false,
            "source": "3",
            "fixed": true
        }, {
            "opacity": 1,
            "source": "4",
            "fixed": false,
            "visibility": true
        }, {
            "opacity": 1.0,
            "name": "geonode:index",
            "title": "index",
            "selected": true,
            "visibility": true,
            "srs": "EPSG:900913",
            "bbox": [13825393.814371249, 807566.643619642, 13852644.846474735, 817795.469341697],
            "getFeatureInfo": {
                "fields": ["GRID_REF", "MINX", "MINY", "MAXX", "MAXY", "Tilename", "File_Path"],
                "propertyNames": {
                    "MAXX": null,
                    "MAXY": null,
                    "GRID_REF": null,
                    "Tilename": null,
                    "MINX": null,
                    "MINY": null,
                    "File_Path": null
                }
            },
            "fixed": false,
            "queryable": true,
            "source": "5"
        }],
        "center": [0.0, -7.081154550627918e-10],
        "units": "m",
        "maxResolution": 156543.03390625,
        "maxExtent": [-20037508.34, -20037508.34, 20037508.34, 20037508.34],
        "zoom": 0,
        "projection": "EPSG:900913"
    },
    "id": 0,
    "sources": {
        "1": {
            "ptype": "gxp_osmsource"
        },
        "0": {
            "ptype": "gxp_olsource"
        },
        "3": {
            "ptype": "gxp_bingsource"
        },
        "2": {
            "ptype": "gxp_mapquestsource"
        },
        "5": {
            "url": "http://cephgeo.lan.dream.upd.edu.ph:8080/geoserver/wms",
            "restUrl": "/gs/rest",
            "ptype": "gxp_wmscsource"
        },
        "4": {
            "ptype": "gxp_mapboxsource"
        }
    }
}


source: ObjectFile_Path: "ftpes://ftp.dream.upd.edu.ph/DL/JE4905/"GRID_REF: "JE4905"MAXX: "650000"MAXY: "806000"MINX: "649000"MINY: "805000"Tilename: "JE4905_1k"
