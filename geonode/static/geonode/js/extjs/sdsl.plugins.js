/*
 To change this license header, choose License Headers in Project Properties.
 To change this template file, choose Tools | Templates
 and open the template in the editor.
 *
 *
    ptype: "sdsl_SearchByBoundBox"
    ptype: "sdsl_SearchByRadius"
 *
 *
 */
/*
 Created on : Augest 06, 2016, 04:45:00 PM
 Author     : Nazmul
 */

Ext.ns("SDSL.plugins");

/**
 * @require plugins/Tool.js
 * @require GeoExt/widgets/Action.js
 * @require OpenLayers/Control/DrawFeature.js
 * @require OpenLayers/Handler/RegularPolygon.js
 * @require OpenLayers/Layer/Vector.js
 * @require OpenLayers/Renderer/SVG.js
 * @require OpenLayers/Renderer/VML.js
 * http://dev.openlayers.org/examples/regular-polygons.html
 * http://www.sitpa.cl:8080/opengeo-docs/webapps/gxp/plugin/action.html
 * http://jsfiddle.net/expedio/L529bqb5/
 */

SDSL.plugins.SearchView = Ext.extend(gxp.plugins.Tool, {

  ptype: "sdsl_SearchView",

  addOutput: function(config) {
    return SDSL.plugins.SearchView.superclass.addOutput.call(this, Ext.apply({
      title: "Box info",
      html: "This is where the box info will be shown"
    }, config));
  }

});

Ext.preg(SDSL.plugins.SearchView.prototype.ptype, SDSL.plugins.SearchView);

SDSL.plugins.SearchByBoundBox = Ext.extend(gxp.plugins.Tool, {

    ptype: "sdsl_SearchByBoundBox",

    boxLayerObj: {},

    addActions: function () {
        var map = this.target.mapPanel.map;
        this.boxLayer = new OpenLayers.Layer.Vector(null, {displayInLayerSwitcher: false});
        map.addLayers([this.boxLayer]);
        // keep our vector layer on top so that it's visible
        map.events.on({
            addlayer: this.raiseLayer,
            scope: this
        });
        var action = new GeoExt.Action({
            //text: "Search by bound box", // BoundBox //rectangle
            //menuText: this.queryMenuText,
            iconCls: "gxp-icon-find",
            tooltip: 'Search by bound box',
            toggleGroup: "draw",
            enableToggle: true,
            map: map,
            control: new OpenLayers.Control.DrawFeature(this.boxLayer,
                OpenLayers.Handler.RegularPolygon, {
                    handlerOptions: {
                        sides: 4,
                        irregular: true
                    }
                }
            )
        });
        return SDSL.plugins.SearchByBoundBox.superclass.addActions.apply(this, [action]);
    },

    raiseLayer: function () {
        var map = this.boxLayer && this.boxLayer.map;
        if (map) {
            map.setLayerIndex(this.boxLayer, map.layers.length);
        }
    }

});
Ext.preg(SDSL.plugins.SearchByBoundBox.prototype.ptype, SDSL.plugins.SearchByBoundBox);

// Search By Radius
SDSL.plugins.SearchByRadius = Ext.extend(gxp.plugins.Tool, {

    ptype: "sdsl_SearchByRadius",

    addActions: function () {

        var that = this;
        var map = this.target.mapPanel.map;
        this.boxLayer = new OpenLayers.Layer.Vector(null, {displayInLayerSwitcher: false});
        map.addLayers([this.boxLayer]);
        // keep our vector layer on top so that it's visible
        map.events.on({
            addlayer: this.raiseLayer,
            scope: this
        });
        //map.events.register("click", this, function (e) {
        //    console.log('click', e.xy.x, e.xy.y);
        //});
        var action = new GeoExt.Action({
            //text: "Search by radius", // Radius //rectangle
            //menuText: this.queryMenuText,
            iconCls: "gxp-icon-find",
            tooltip: 'Search by radius',
            toggleGroup: "draw",
            enableToggle: true,
            map: map,
            handler: function (button, event) {
                //console.log(button, event);
            },
            control: new OpenLayers.Control.DrawFeature(this.boxLayer,
                OpenLayers.Handler.RegularPolygon, {
                    handlerOptions: {
                        sides: 40
                    }
                }
            )
        });
        action.control.events.register('featureadded', this, function (e) {
            //console.log('featureadded event fire', e);
            // DRY-principle not applied
            var f = e.feature;
            // ###############
            // get pixel value
            // ###############
            /*var geometry = f.geometry;
             var coordinate = new OpenLayers.LonLat(geometry.x, geometry.y);
             var pixel = f.layer.map.getPixelFromLonLat(coordinate);
             console.log(geometry.x, geometry.y, pixel);*/
            //calculate the min/max coordinates of a circle
            var minX = f.geometry.bounds.left;
            var minY = f.geometry.bounds.bottom;
            var maxX = f.geometry.bounds.right;
            var maxY = f.geometry.bounds.top;
            //calculate the center coordinates
            var startX = (minX + maxX) / 2;
            var startY = (minY + maxY) / 2;
            // ########################################
            //make two points at center and at the edge
            // ########################################
            var startPoint = new OpenLayers.Geometry.Point(startX, startY);
            var endPoint = new OpenLayers.Geometry.Point(maxX, startY);
            var radius = new OpenLayers.Geometry.LineString([startPoint, endPoint]);
            // #########################################################
            //console.log('getResolution', f.layer.map.getResolution());
            //calculate length. WARNING! The EPSG:900913 lengths are meaningless except around the equator. Either use a local coordinate system like UTM, or geodesic calculations.
            // #########################################################
            var len = Math.round(radius.getLength()).toString();
            var radiusInMeter = len;
            var radiusInPixel = parseInt(len / f.layer.map.getResolution());
            //console.log('radiusInPixel', radiusInPixel);
            // ####################
            // Get Search Layer URL
            // Get Search Layer URL
            // ####################
            var searchLayerList = [];
            var mLayers = f.layer.map.layers;
            for (var a = 0; a < mLayers.length; a++) {
                if ((mLayers[a].url != undefined) && (typeof mLayers[a].url === 'string')) {
                    searchLayerList.push(mLayers[a]);
                }
            }
            /*for(var a = 0; a < searchLayerList.length; a++ ){
             console.log('searchLayerList', a, searchLayerList[a].name, searchLayerList[a].url);
             }*/
            // ##################
            // get center lat lon
            // get center lat lon
            // ##################
            var mapProjection = new OpenLayers.Projection(f.layer.map.projection);
            var projDisplayObj = new OpenLayers.Projection("EPSG:4326");
            var centerPoint = startPoint.clone().transform(mapProjection, projDisplayObj);


            // get center position clientXY pixel
            var pixel = {x: 0, y: 0};
            var mapBound = f.layer.map.getExtent();
            var mbMinX = mapBound.left;
            var mbMinY = mapBound.bottom;
            var mbMaxX = mapBound.right;
            var mbMaxY = mapBound.top;
            var size = f.layer.map.size;
            var xPx = (((size.w) * (startPoint.x - mbMinX)) / (mbMaxX - mbMinX));
            var yPx = (((size.h) * (startPoint.y - mbMinY)) / (mbMaxY - mbMinY));
            //console.log('center position ::', xPx, yPx);
            pixel.x = parseInt(xPx);
            pixel.y = parseInt(yPx);
            /*var coordinate = new OpenLayers.LonLat(centerPoint.x, centerPoint.y);
             var pixel = f.layer.map.getPixelFromLonLat(coordinate);
             var viewPixel = f.layer.map.getViewPortPxFromLonLat(coordinate);
             console.log([startPoint, centerPoint, pixel, viewPixel]);*/
            if (searchLayerList.length > 0) {
                this.getFeatureInfo(searchLayerList, pixel, radiusInPixel, radiusInMeter, centerPoint);
            }
            // ###############
            //style the radius
            //style the radius
            // ###############
            var punktstyle = {
                strokeColor: "red",
                strokeWidth: 2,
                pointRadius: 5,
                fillOpacity: 0.2
            };
            var style = {
                strokeColor: "#0500bd",
                strokeWidth: 3,
                label: len + " m",
                labelAlign: "left",
                labelXOffset: "20",
                labelYOffset: "10",
                labelOutlineColor: "white",
                labelOutlineWidth: 3
            };
            // ################################
            //add radius feature to radii layer
            //add radius feature to radii layer
            // ################################
            var centerPointDrawing = new OpenLayers.Feature.Vector(startPoint, {}, punktstyle);
            var radiusLineDrawing = new OpenLayers.Feature.Vector(radius, {'length': len}, style);
            // action control deactivate when draw done
            action.control.deactivate();
            // ##############################
            // draw radius on selected circle
            // draw radius on selected circle
            // ##############################
            //this.boxLayer.addFeatures([centerPointDrawing, radiusLineDrawing]);
            //this.boxLayer.addFeatures([radiusLineDrawing]);
            var map = this.boxLayer && this.boxLayer.map;
            if (map) {
                map.setLayerZIndex(this.boxLayer, 500);
            }
        });
        action.control.handler.callbacks.move = function (e) {
            //console.log('move event fire', e);
            var linearRing = new OpenLayers.Geometry.LinearRing(e.components[0].components);
            var geometry = new OpenLayers.Geometry.Polygon([linearRing]);
            var polygonFeature = new OpenLayers.Feature.Vector(geometry, null);
            var polybounds = polygonFeature.geometry.getBounds();

            var minX = polybounds.left;
            var minY = polybounds.bottom;
            var maxX = polybounds.right;
            var maxY = polybounds.top;

            //calculate the center coordinates

            var startX = (minX + maxX) / 2;
            var startY = (minY + maxY) / 2;

            //make two points at center and at the edge
            var startPoint = new OpenLayers.Geometry.Point(startX, startY);
            var endPoint = new OpenLayers.Geometry.Point(maxX, startY);
            var radius = new OpenLayers.Geometry.LineString([startPoint, endPoint]);
            var len = Math.round(radius.getLength()).toString();

            var laenge, einheit;
            if (len > 1000) {
             laenge = len / 1000;
             laenge = laenge.toFixed(2);
             einheit = "km";
            } else {
             laenge = len;
             einheit = "m";
            }
            // ###############
            //style the radius
            //style the radius
            // ###############
            var punktstyle = {
                strokeColor: "red",
                strokeWidth: 1,
                pointRadius: 4,
                fillOpacity: 0.2
            };
            var styleLabel = laenge + " " + einheit;
            var style = {
                strokeColor: "#0500bd",
                strokeWidth: 3,
                label: styleLabel,
                labelAlign: "left",
                labelXOffset: "20",
                labelYOffset: "10",
                labelOutlineColor: "white",
                labelOutlineWidth: 3
            };
            // ################################
            //add radius feature to radii layer
            //add radius feature to radii layer
            // ################################
            var centerPointDrawing = new OpenLayers.Feature.Vector(startPoint, {}, punktstyle);
            var radiusLineDrawing = new OpenLayers.Feature.Vector(radius, {'length': len}, style);
            // action control deactivate when draw done
            //action.control.deactivate();
            // ##############################
            // draw radius on selected circle
            // draw radius on selected circle
            // ##############################
            that.boxLayer.destroyFeatures();
            that.boxLayer.addFeatures([centerPointDrawing, radiusLineDrawing]);
            //this.boxLayer.addFeatures([radiusLineDrawing]);
        }
        return SDSL.plugins.SearchByRadius.superclass.addActions.apply(this, [action]);
    },
    getFeatureInfoRequestWMSParams: function (layer, pixel) {
        //console.log('layer', layer);
        // ###################
        // get extent for bbox
        // ###################
        var extent = layer.getExtent();
        var projDisplayObj = new OpenLayers.Projection("EPSG:4326");
        var extentLatLonObj = extent.clone().transform(layer.projection, projDisplayObj);
        // #################
        // get layer map obj
        // #################
        var size = layer.map.size;
        // ###################
        // get params of layer
        // ###################
        var params = layer.params;

        // ##############
        // Make request params
        // ##############
        var requestParams = {};
        requestParams.info_format = 'application/json';
        requestParams.REQUEST = 'GetFeatureInfo';
        requestParams.SERVICE = params.SERVICE || '';
        requestParams.VERSION = params.VERSION || '';
        requestParams.LAYERS = params.LAYERS || layer.name || '';
        //requestParams.layers = layer.name || '';
        requestParams.styles = params.styles || '';
        //requestParams.SRS = params.SRS || '';
        requestParams.SRS = 'EPSG:4326';
        requestParams.BBOX = extentLatLonObj.toBBOX() || '';
        requestParams.width = size.w || '';
        requestParams.height = size.h || '';
        requestParams.query_layers = params.LAYERS || layer.name || '';
        requestParams.x = pixel.x || '';
        requestParams.y = pixel.y || '';
        requestParams.EXCEPTIONS = 'application/vnd.ogc.se_xml';
        requestParams.feature_count = 50;

        // debug code
        /*console.log(requestParams);
         console.log('RequestParams String :: ');
         console.log(JSON.stringify(requestParams));*/

        return requestParams;
    },
    getFeatureInfoRequestWFSParams: function (layer, radiusInMeter, centerPoint) {
        var centerLat = centerPoint.y;
        var centerLon = centerPoint.x;
        var drg = (radiusInMeter/111325);
        var cqlFilter='DWithin(the_geom,POINT('+centerLon+' '+centerLat+'),'+drg+',meters)';
        // ###################
        // get params of layer
        // ###################
        var params = layer.params;

        // ##############
        // Make request params
        // ##############
        var requestParams = {};
        requestParams.service = 'WFS';
        requestParams.version = '1.0.0';
        requestParams.request = 'GetFeature';
        requestParams.outputFormat = 'JSON';
        requestParams.srsName = 'EPSG:4326';
        requestParams.typeNames = params.LAYERS || layer.name || '';
        requestParams.cql_filter = cqlFilter;

        return requestParams;
    },
    getFeatureInfoRequestWMSUrl: function (layer) {
        var url = layer.url;
        var uri = url.split('/wms');
        return uri[0] + '/wms';
    },
    getFeatureInfoRequestWFSUrl: function (layer) {
        var url = layer.url;
        //console.log(url);
        var uri = url.split('/wms?');
        return uri[0] + '/wfs';
    },
    getFeatureInfo: function (searchLayerList, pixel, radiusInPixel, radiusInMeter, centerPoint) {
        for (var i = 0; i < searchLayerList.length; i++) {
            var layer = searchLayerList[i];
            //console.log('layer :: ',layer);
            // request for WMS
            /*var url = this.getFeatureInfoRequestWMSUrl(layer);
            var parameter = this.getFeatureInfoRequestWMSParams(layer, pixel);
            parameter.buffer = radiusInPixel;*/
            // request for WFS
            if(layer.visibility){
                var url = this.getFeatureInfoRequestWFSUrl(layer);
                var parameter = this.getFeatureInfoRequestWFSParams(layer, radiusInMeter, centerPoint);

                var thatObj = this;

                //console.log(parameter);
                // Basic request
                Ext.Ajax.request({
                    url: url,
                    method: "GET",
                    params: parameter,
                    success: function (response, data) {
                        //console.log('success responseText');
                        //console.log(response.responseText);
                        //console.log(parameter, data);
                        var layerTitle = (data !== undefined && data.params !== undefined && data.params.typeNames !== undefined) ? data.params.typeNames : null;
                        thatObj.addOutput(parameter, response.responseText, centerPoint, layerTitle);
                    },
                    failure: function (error) {
                        console.log('failure', error);
                    }
                });
            }
        }
    },

    raiseLayer: function () {
        //console.log('raiseLayers');
        this.boxLayer.destroyFeatures();
        var map = this.boxLayer && this.boxLayer.map;
        if (map) {
            map.setLayerZIndex(this.boxLayer, 500);
            //map.setLayerIndex(this.boxLayer, map.layers.length);
            //map.raiseLayer(this.boxLayer, 500);
        }
    },

    /** api: method[addOutput]
     */

    addOutput: function (parameter, response, centerPoint, layerTitle) {
        //console.log('out');
        var gridTitle = parameter.typeNames;
        if(layerTitle !== undefined && layerTitle !== null && layerTitle !== ''){
            gridTitle = layerTitle;
        }
        var columnsLen = 0;
        var tableHeaderIds = [];
        var tableHeader = [];
        var tableField = [];
        var tableRows = [];
        var loadGridData = false;

        var data = Ext.decode(response);
        var isPointLayer = false;
        var totalResult = 0;
        if (data != undefined && data.features != undefined) {
            var features = data.features;
            var len = features.length;
            totalResult = len;
            if (len > 0) {
                console.log('total len', len);
                for (var i = 0; i < len; i++) {
                    var centerLat = centerPoint.y;
                    var centerLon = centerPoint.x;
                    var coordinates = [];
                    if(features[i].geometry != undefined){
                        var geometry = features[i].geometry;
                        if(geometry.type != undefined && (geometry.type == 'Point' || geometry.type == 'point')){
                            isPointLayer = true;
                            if(isPointLayer && !(tableHeaderIds.indexOf('centerDistance') > -1)){
                                var header = {
                                    id: 'centerDistance',
                                    header: 'Distance',
                                    sortable: true,
                                    dataIndex: 'centerDistance'
                                };
                                tableHeaderIds.push('centerDistance');
                                tableHeader.push(header);
                                tableField.push({name: 'centerDistance'});
                            }
                            if(geometry.coordinates != undefined){
                                coordinates = geometry.coordinates;
                            }
                        }
                    }
                    if(features[i].properties != undefined){
                        var properties = features[i].properties;
                        if ((properties instanceof Object) && !(properties instanceof Array)) {
                            var keys = Object.keys(properties);
                            columnsLen = keys.length;
                            var headerColumnsLen = columnsLen;
                            //var tableRow = [];
                            var tableRow = {};
                            if(isPointLayer){
                                var distance = 'N/A';
                                if(coordinates[0] != undefined && coordinates[1] != undefined){
                                    distance = this.getPointDistance(centerLat, centerLon, coordinates[1], coordinates[0]);
                                    //console.log(centerLat, centerLon, coordinates[1], coordinates[0], distance);
                                    //tableRow.push(distance);
                                    tableRow.centerDistance = distance;
                                } else {
                                    //tableRow.push(distance);
                                    tableRow.centerDistance = distance;
                                }
                                headerColumnsLen = headerColumnsLen+1;
                            }
                            for (var j = 0; j < columnsLen; j++) {
                                var proName = keys[j];
                                //tableRow.push(properties[proName]);
                                tableRow['pro_'+proName+'_perty'] = properties[proName] + '';
                                if (tableHeader.length < headerColumnsLen) {
                                    var header = {
                                        id: 'pro_'+proName+'_perty',
                                        header: proName,
                                        sortable: true,
                                        dataIndex: 'pro_'+proName+'_perty'
                                    };
                                    tableHeaderIds.push(proName);
                                    tableHeader.push(header);
                                    var field = {
                                        name: 'pro_'+proName+'_perty'
                                    };
                                    tableField.push(field);
                                }
                            }
                            tableRows.push(tableRow);
                        }
                    }
                }
                loadGridData = true;
            }
        }

        //console.log('tableHeaderIds', tableHeaderIds);
        //console.log('tableHeader', tableHeader);
        //console.log('tableField', tableField);
        //console.log('tableRows', tableRows.length);
        //console.log('tableRows', tableRows[0]);
        //console.log('tableRows', tableRows[2]);
        //console.log('tableRows', tableRows[5]);

        if(loadGridData){
            /*tableRows = tableRows.sort(function(a, b){
                if(parseFloat(a[0]) == NaN && typeof a[0] === 'string' || a[0] instanceof String)
                    return false;
                else
                    return parseFloat(a[0]) - parseFloat(b[0]);
            });*/
            var PAGE_SIZE = 10;

            // make MemoryProxy
            var dataSet = {};
            dataSet.records = tableRows;
            dataSet.totalCount = tableRows.length;

            // create the Data Store
            var store = new Ext.data.JsonStore({
                root: 'records',
                totalProperty: 'totalCount',
                //idProperty: 'centerDistance',
                fields: tableField,
                proxy: new Ext.data.MemoryProxy(dataSet)
            });
            //console.log(dataSet);
            if(isPointLayer){
                store.setDefaultSort('centerDistance', 'asc'); //desc
            }
            // trigger the data store load
            store.load({params:{start:0, limit:PAGE_SIZE}});
            // create the Grid
            var grid = new Ext.grid.GridPanel({
                layout:'fit',
                store: store,
                header: true,
                colModel: new Ext.grid.ColumnModel({
                    default: {
                        sortable: true
                    },
                    columns: tableHeader
                }),
                footer: true, //'Total result: '+totalResult,
                //autoScroll: true,
                trackMouseOver:false,
                disableSelection:true,
                loadMask: true,
                //stripeRows: true,
                //maxHeight: 350,
                height: 400,
                //width: 600,
                title: gridTitle,
                //frame: true,
                // config options for stateful behavior
                //stateful: true,
                //stateId: 'grid'
                // paging bar on the bottom
                // customize view config
                //autoHeight: true,
                //style: "top: auto; bottom: 0",
                bbar: new Ext.PagingToolbar({
                    pageSize: PAGE_SIZE,
                    store: store,
                    displayInfo: true,
                    displayMsg: 'Displaying topics {0} - {1} of {2}',
                    emptyMsg: "No topics to display",
                    items: {
                        text: 'Download CSV',
                        iconCls: "icon-save",
                        handler: function () {
                            //var extGridExporter = new ExtGridExporter();
                            //extGridExporter.exportGrid(grid);
                            this.downloadCSV(tableRows, { filename: gridTitle+".csv" });
                        },
                        scope: this
                    }
                })
            });
            // render it
            //grid.render('records-grid');
            // trigger the data store load
            //store.load({params:{start:0, limit:PAGE_SIZE}});
            var outconfig = {
                border: false,
                layout: "fit",
                height: 400,
                maxHeight: 400,
                width: 600,
                items: [
                    grid
                ],
                /*bbar: ["->", {
                    text: 'Save',
                    iconCls: "icon-save",
                    handler: function () {
                        GridExporter.exportGrid(grid);
                    },
                    scope: this
                }],
                listeners: {
                    afterlayout: function () {
                        var height = Ext.getBody().getViewSize().height;
                        if (this.getHeight() > height) {
                            this.setHeight(height);
                        }
                        this.center();
                    },
                    afterrender: function () {
                        var height = Ext.getBody().getViewSize().height;
                        if (this.getHeight() > height) {
                            this.setHeight(height);
                        }
                        this.center();
                    }
                }*/
            };
            //var config = Ext.apply(grid, config || {});
            var config = Ext.apply(outconfig, config || {});
        }
        //return SDSL.plugins.SearchByRadius.superclass.addActions.apply(this, [action]);
        var queryForm = SDSL.plugins.SearchByRadius.superclass.addOutput.call(this, config);
    },

    getPointDistance: function (p1Lat, p1Lng, p2Lat, p2Lng) {
        var R = 6378137; // Earth’s mean radius in meter
        var dLat = this.getRad(p2Lat - p1Lat);
        var dLong = this.getRad(p2Lng - p1Lng);
        var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                Math.cos(this.getRad(p1Lat)) * Math.cos(this.getRad(p2Lat)) *
                Math.sin(dLong / 2) * Math.sin(dLong / 2);
        var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        var d = R * c;
        var km = (d/1000);
        //var mile = this.getMeterToMiles(d);
        return km.toFixed(2); // returns the distance in meter
    },

    getRad: function (x) {
        return x * Math.PI / 180;
    },

    getMeterToMiles: function (meter) {
        return meter * 0.000621371192;
    },

    getMileToMeters: function (mile) {
        return mile * 1609.344;
    },

    convertArrayOfObjectsToCSV: function (args) {
        var result, ctr, keys, columnDelimiter, lineDelimiter, data;

        data = args.data || null;
        if (data == null || !data.length) {
            return null;
        }

        columnDelimiter = args.columnDelimiter || ',';
        lineDelimiter = args.lineDelimiter || '\n';

        var headerItem = [];
        var keyItems = Object.keys(data[0]);
        for(var i=0; i<keyItems.length; i++){
            var item = keyItems[i];
            item = item.replace('centerDistance', 'Distance')
                .replace('pro_', '')
                .replace('_perty','');
            headerItem.push(item);
        }
        keys = Object.keys(data[0]);

        result = '';
        result += headerItem.join(columnDelimiter);
        result += lineDelimiter;

        data.forEach(function (item) {
            ctr = 0;
            keys.forEach(function (key) {
                if (ctr > 0)
                    result += columnDelimiter;

                result += item[key];
                ctr++;
            });
            result += lineDelimiter;
        });

        return result;
    },

    downloadCSV: function (stockData, args) {
        var data, filename, link;

        var csv = this.convertArrayOfObjectsToCSV({
            data: stockData
        });
        if (csv == null)
            return;

        filename = args.filename || 'export.csv';

        if (!csv.match(/^data:text\/csv/i)) {
            csv = 'data:text/csv;charset=utf-8,' + csv;
        }
        data = encodeURI(csv);

        link = document.createElement('a');
        link.setAttribute('href', data);
        link.setAttribute('download', filename);
        //link.click();
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

});
Ext.preg(SDSL.plugins.SearchByRadius.prototype.ptype, SDSL.plugins.SearchByRadius);