
var XB = XB || {};  // global used for xblock adapter scripts

/*
 *  These are all the functions which get data to/from worldmap and communicate it back to the xblock adapter
 *
 *  It sets up layers on the map for drawing polygons and polylines and deals with highlighting geometry on the
 *  map as well as setting up the map to draw polygons, polylines and markerplacements so that on completion
 *  the data can be sent back to the xblock adapter.
 *
 */

XB.markers = new Array();
XB.polygons = new Array();
XB.polylines = new Array();

XB.currentQuestion = null;  //what we're currently searching for with the currently selected tool

XB.clickControl = OpenLayers.Class(OpenLayers.Control, {
    defaultHandlerOptions: {
        'single': true,
        'double': false,
        'pixelTolerance': 0,
        'stopSingle': false,
        'stopDouble': false
    },

    initialize: function (options) {
        this.handlerOptions = OpenLayers.Util.extend(
                {}, this.defaultHandlerOptions
        );
        OpenLayers.Control.prototype.initialize.apply(
                this, arguments
        );
        this.handler = new OpenLayers.Handler.Click(
                this, {
                    'click': this.trigger
                }, this.handlerOptions
        );
    },

    trigger: function (e) {
        var map = e.object;
        var lonlat = map.getLonLatFromPixel(e.xy);
        var point = XB.transformToLonLat(lonlat);

        var size = new OpenLayers.Size(21, 25);
        var offset = new OpenLayers.Pixel(-size.w / 2, -size.h);
        var icon = new OpenLayers.Icon('/static/geonode/externals/ext/resources/images/default/xblock-images/marker.png', size, offset);
        icon.imageDiv.firstChild.setAttribute("style", "background-color:" + XB.currentQuestion.color);

        if (XB.markers[XB.currentQuestion.id]) {
            XB.markerLayer.removeMarker(XB.markers[XB.currentQuestion.id]);
        }
        XB.markers[XB.currentQuestion.id] = new OpenLayers.Marker(lonlat, icon);
        XB.markerLayer.addMarker(XB.markers[XB.currentQuestion.id]);

        XB.MESSAGING.getInstance().send(
                new Message("point_response",
                        {
                            point: {lon: point.x, lat: point.y},
                            question: XB.currentQuestion
                        }
                )
        );
    }
});

XB.getLayerLegendInfo = function(layers, layer) {
    for (var i = 0; i < layers.length; i++) {
        if (layers[i].styles) {
            if (layers[i].title === layer.name) {
                return {
                    styles: layers[i].styles,
                    name: layers[i].name,
                    url: layers[i].url
                }
            }
        }
    }
    return null;
}

XB.geographicProjection = new OpenLayers.Projection("EPSG:4326");
XB.mercatorProjection =   new OpenLayers.Projection("EPSG:900913");
XB.transformToXY = function(lonlat) {
    return new OpenLayers.Geometry.Point(lonlat.lon, lonlat.lat).transform(XB.geographicProjection, XB.mercatorProjection);
}

XB.transformToLonLat=function(lonlat) {
    return new OpenLayers.Geometry.Point(lonlat.lon, lonlat.lat).transform(XB.mercatorProjection, XB.geographicProjection);
}
//************************************ END - XBLOCK RELATED FUNCTIONS ***********************************************


XB.xblocktools = function () {

    XB.markerLayer = new OpenLayers.Layer.Markers("worldmap-markers");
    XB.polygonLayer = new OpenLayers.Layer.Vector("worldmap-polygons", {
        styleMap: new OpenLayers.StyleMap({
            fillColor: "#ff0000",
            fillOpacity: 0.3
        })
    });
    XB.polylineLayer = new OpenLayers.Layer.Vector("worldmap-polyline", {
        styleMap: new OpenLayers.StyleMap({
            strokeColor: "#000000",
            strokeOpacity: 1.0,
            strokeWidth: 3
        })
    });

    XB.polygonControl =
            new OpenLayers.Control.DrawFeature(XB.polygonLayer, OpenLayers.Handler.Polygon, {
                callbacks: {
                    done: function (geo) {
                        var polygon = [];
                        for (var i = 0; i < geo.components[0].components.length; i++) {
                            var point = XB.transformToLonLat({lon: geo.components[0].components[i].x, lat: geo.components[0].components[i].y});
                            polygon.push({lon: point.x, lat: point.y});
                        }

                        XB.MESSAGING.getInstance().send(
                                new Message("polygon_response",
                                        {
                                            polygon: polygon,
                                            question: XB.currentQuestion
                                        }
                                )
                        );

                        var feature = new OpenLayers.Feature.Vector(geo, {}, {
                            fillColor: '#' + XB.currentQuestion.color,
                            fillOpacity: 0.4
                        });
                        var proceed = this.events.triggerEvent("sketchcomplete", {feature: feature});
                        if (proceed !== false) {
                            feature.state = OpenLayers.State.INSERT;
                            if (XB.polygons[XB.currentQuestion.id]) {
                                XB.polygonLayer.removeFeatures([XB.polygons[XB.currentQuestion.id]]);
                            }
                            XB.polygons[XB.currentQuestion.id] = feature;
                            XB.polygonLayer.addFeatures([feature]);
                            this.featureAdded(feature);
                            this.events.triggerEvent("featureadded", {feature: feature});
                        }

                    }
                }
            });

    XB.polylineControl =
            new OpenLayers.Control.DrawFeature(XB.polylineLayer, OpenLayers.Handler.Path, {
                doubleTouchTolerance: 50,
                callbacks: {
                    done: function (geo) {
                        var polyline = [];
                        for (var i = 0; i < geo.components.length; i++) {
                            var point = XB.transformToLonLat({lon: geo.components[i].x, lat: geo.components[i].y});
                            polyline.push({lon: point.x, lat: point.y});
                        }

                        XB.MESSAGING.getInstance().send(
                                new Message("polyline_response",
                                        {
                                            polyline: polyline,
                                            question: XB.currentQuestion
                                        }
                                )
                        );

                        var feature = new OpenLayers.Feature.Vector(geo, {}, {
                            strokeColor: '#' + XB.currentQuestion.color,
                            strokeOpacity: 1,
                            strokeWidth: 3
                        });
                        var proceed = this.events.triggerEvent("sketchcomplete", {feature: feature});
                        if (proceed !== false) {
                            feature.state = OpenLayers.State.INSERT;
                            if (XB.polylines[XB.currentQuestion.id]) {
                                XB.polylineLayer.removeFeatures([XB.polylines[XB.currentQuestion.id]]);
                            }
                            XB.polylines[XB.currentQuestion.id] = feature;
                            XB.polylineLayer.addFeatures([feature]);
                            this.featureAdded(feature);
                            this.events.triggerEvent("featureadded", {feature: feature});
                        }
                    }
                }
            });

    app.mapPanel.map.addLayers([XB.markerLayer, XB.polygonLayer, XB.polylineLayer]);

    app.mapPanel.map.events.register("moveend", app.mapPanel, function () {
        // calculate lat/lon
        XB.MESSAGING.getInstance().send(new Message("moveend", {center: XB.transformToLonLat(app.mapPanel.map.getCenter()), zoomLevel: app.mapPanel.map.getZoom()}));
    });

    app.mapPanel.map.events.register("zoomend", app.mapPanel.map, function () {
        XB.MESSAGING.getInstance().send(new Message("zoomend", app.mapPanel.map.getZoom()));
    });

    app.mapPanel.map.events.register("changelayer", app.mapPanel.map, function (e) {
        var msg = new Message("changelayer", {name: e.layer.name, id: e.layer.id, visibility: e.layer.visibility, opacity: e.layer.opacity, legendData: XB.getLayerLegendInfo(app.config.map.layers, e.layer)});
        console.log("sending changelayer back to master.  layer: " + JSON.stringify(msg.getMessage()));
        XB.MESSAGING.getInstance().send(msg);
    });

    XB.MESSAGING.getInstance().registerHandler("setZoomLevel", function (m) {
        app.mapPanel.map.zoomTo(m.getMessage());
    });
    XB.MESSAGING.getInstance().registerHandler("setCenter", function (m) {
        var data = m.getMessage();
        //Ext.example.msg("Info","setCenter: "+data.centerLat+","+data.centerLon+"   zoom="+data.zoomLevel);
        var pt = XB.transformToXY({lon: data.centerLon, lat: data.centerLat});
        app.mapPanel.map.setCenter([pt.x, pt.y], data.zoomLevel, false, false);
    });
    XB.MESSAGING.getInstance().registerHandler("setLayers", function (m) {
        console.log("slave recieved setLayers command, data = " + m.getMessage());
        var data = JSON.parse(m.getMessage());
        for (var id in data) {
            try {
                if (id !== "OpenLayers_Layer_Vector_132") {  //TODO: REMOVE THIS - it causes an exception that we can't seem to handle
                    var layer = app.mapPanel.map.getLayer(id);
                    if (layer != null) {
                        //  layer.setVisibility(data[id]['visibility']);
                        var ctrl = Ext.getCmp("layer_menu_" + layer.id);
                        layer.setOpacity(data[id]['opacity']);
                        if ((ctrl.checked && !data[id]['visibility']) || (!ctrl.checked && data[id]['visibility'])) {
                            console.log("turning layer: " + id + " to " + data[id]['visibility']);
                            ctrl.setChecked(data[id]['visibility']);
                        }
                        else {
                            console.log("didn't change visibility for layer: " + id + " currently: " + data[id]['visibility']);
                            console.log("sending changelayer back to master.  layer: { name: " + data[id]['name'] + ", id: " + id + ", visibility: " + data[id]['visibility'] + ", opacity: " + data[id]['opacity'] + ",  legendData: " + JSON.stringify(XB.getLayerLegendInfo(app.config.map.layers, data[id])) + "}");
                            XB.MESSAGING.getInstance().send(new Message("changelayer", {name: data[id]['name'], id: id, visibility: data[id]['visibility'], opacity: data[id]['opacity'], legendData: XB.getLayerLegendInfo(app.config.map.layers, data[id])}));
                        }
                    } else {
                        console.log("ERROR: could not find layer for id: " + id);
                    }
                } else {
                    console.log("setLayer was asked to deal with a bad layer: " + id);
                }
            } catch (e) {
                console.log("slave caught exception during setLayers: " + e);
            }
        }
    });

    XB.markerControl = new XB.clickControl();
    app.mapPanel.map.addControl(XB.markerControl);
    app.mapPanel.map.addControl(XB.polygonControl);
    app.mapPanel.map.addControl(XB.polylineControl);

    XB.MESSAGING.getInstance().registerHandler("reset-answer-tool", function (m) {
        $('.olMapViewport').css('cursor', "default");
//           if( document.getElementById(id) != undefined ) {
//               document.getElementById(id).style.cursor = "default";
//           }
        XB.markerControl.deactivate();
        XB.polygonControl.deactivate();
        XB.polylineControl.deactivate();
        XB.currentQuestion = null;
    });

    XB.MESSAGING.getInstance().registerHandler("set-answer-tool", function (e) {

        var message = JSON.parse(e.message);
        XB.currentQuestion = message;

        //TODO: fix url - make relative
        //should use   $('.olMapViewport').style.cursor = "url(http://robertlight.com/tmp/"+XB.currentQuestion.type+"Cursor.png) 16 16, auto";
        $('.olMapViewport').css('cursor', "url(/static/geonode/externals/ext/resources/images/default/xblock-images/" + XB.currentQuestion.type + "Cursor.png) 16 16, auto");
        //document.getElementById(app.mapPanel.map.id+"_OpenLayers_ViewPort").style.cursor = "url(http://robertlight.com/tmp/"+XB.currentQuestion.type+"Cursor.png) 16 16, auto";
        if (XB.currentQuestion.type == 'point') {
            Ext.example.msg("Info", "{% trans 'Click the map at the location requested' %}");
            XB.markerControl.activate();
        } else if (XB.currentQuestion.type == 'polygon') {
            // window.alert("color="+XB.currentQuestion.color);
            XB.polygonLayer.styleMap = new OpenLayers.StyleMap({
                fillColor: '#' + XB.currentQuestion.color,
                fillOpacity: 0.3
            });
            Ext.example.msg("Info", "{%  trans 'Please click on the boundaries of a polygon. <br/> Double - click to end drawing.' %}");
            XB.polygonControl.activate();
        } else if (XB.currentQuestion.type == 'polyline') {
            Ext.example.msg("Info", "{%  trans 'Please click on the verticies of a polyline.</br/>Double - click  to end drawing.' %}");
            XB.polylineControl.activate();
        }

    });

    XB.MESSAGING.getInstance().registerHandler("flash-polygon", function (e) {
        var data = JSON.parse(e.message);
        var features = [];
        var bounds = null;
        for (var i = 0; i < data.length; i++) {
            var points = [];
            for (var j = 0; j < data[i].length; j++) {
                points.push(XB.transformToXY(data[i][j]));
            }
            var ring = new OpenLayers.Geometry.LinearRing(points);
            var center = ring.getCentroid();
            var feature =
                    new OpenLayers.Feature.Vector(
                            new OpenLayers.Geometry.Polygon(ring),
                            {},
                            {
                                fillColor: '#FF0000',
                                fillOpacity: 0.05,
                                strokeColor: '#FF0000',
                                strokeOpacity: 0.05
                            }
                    );
            feature.state = OpenLayers.State.INSERT;
            var b = ring.getBounds();
            if (bounds != null) {
                bounds.extend(b);
            } else {
                bounds = b;
            }
            features.push(feature);
        }

        app.mapPanel.map.setCenter(
                [center.x, center.y],
                Math.min(15, app.mapPanel.map.getZoomForExtent(bounds, false))
        );
        XB.polygonLayer.addFeatures(features);
        XB.polygonLayer.redraw();
        setTimeout(function () {
            XB.polygonLayer.removeFeatures(features);
            XB.polygonLayer.redraw();
        }, 3000);

    });

    XB.MESSAGING.getInstance().registerHandler("reset-highlights", function (m) {
        try {
            XB.polygonLayer.destroyFeatures();
        } catch (e) {
        }
        try {
            XB.markerLayer.destroyFeatures();
        } catch (e) {
        }
        try {
            XB.polylineLayer.destroyFeatures();
        } catch (e) {
        }
        try {
            XB.markerLayer.clearMarkers();
        } catch (e) {
        }
    });

    XB.MESSAGING.getInstance().registerHandler("highlight-layer", function (m) {
        var data = JSON.parse(m.getMessage());
        var layer = app.mapPanel.map.getLayer(data['layer']);
        var duration = data['duration'];
        if (layer != null) {
            var ctrl = Ext.getCmp("layer_menu_" + data['layer']);
            if (!ctrl.checked) {
                ctrl.setChecked(true);
            }
            var zoom = app.mapPanel.map.getZoomForExtent(layer.maxExtent, true) + data['relativeZoom'];
            app.mapPanel.map.setCenter(layer.maxExtent.getCenterLonLat(), zoom);
            if (duration != undefined && duration > 0) {
                setTimeout(function () {
                    ctrl.setChecked(false);
                }, duration);
            }
        } else {
            console.log("ERROR: could not find layer for id: " + id);
        }
    });

    XB.MESSAGING.getInstance().registerHandler("highlight-geometry", function (e) {
        var data = JSON.parse(e.message);
        var type = data['type'];
        var duration = data['duration']
        var features = [];
        var relativeZoom = data['relativeZoom'] == undefined ? 0 : data['relativeZoom'];
        var bounds = null;
        if (type == 'polygon') {
            var points = [];
            for (var i = 0; i < data['points'].length; i++) {
                points.push(XB.transformToXY(data['points'][i]))
            }
            var ring = new OpenLayers.Geometry.LinearRing(points);
            var center = ring.getCentroid();
            var feature =
                    new OpenLayers.Feature.Vector(
                            new OpenLayers.Geometry.Polygon(ring),
                            {},
                            {
                                fillColor: '#FF0000',
                                fillOpacity: 0.5,
                                strokeColor: '#FF0000',
                                strokeOpacity: 0.5
                            }
                    );
            feature.state = OpenLayers.State.INSERT;
            bounds = ring.getBounds();
            features.push(feature);

            var factor = Math.min(15, relativeZoom + app.mapPanel.map.getZoomForExtent(bounds, false));
            console.log("zooming in to (" + center.x + "," + center.y + ") factor=" + factor);
            app.mapPanel.map.setCenter([center.x, center.y], factor);

            XB.polygonLayer.addFeatures(features);
            XB.polygonLayer.redraw();
            if (duration != undefined && duration > 0) {
                setTimeout(function () {
                    XB.polygonLayer.removeFeatures(features);
                    XB.polygonLayer.redraw();
                }, duration);
            }
        } else if (type == 'point') {
            // app.mapPanel.map
            var size = new OpenLayers.Size(21, 25);
            var offset = new OpenLayers.Pixel(-size.w / 2, -size.h);
            var xy = XB.transformToXY(data['points'][0]);
            var icon = new OpenLayers.Icon('/static/geonode/externals/ext/resources/images/default/xblock-images/marker.png', size, offset);
            app.mapPanel.map.setCenter([xy.x, xy.y], 11 + relativeZoom);
            marker = new OpenLayers.Marker({lon: xy.x, lat: xy.y}, icon);
            XB.markerLayer.addMarker(marker);
            if (duration != undefined && duration > 0) {
                setTimeout(function () {
                    XB.markerLayer.removeMarker(marker);
                }, duration);
            }
        } else if (type == 'polyline') {
            var points = [];
            for (var i = 0; i < data['points'].length; i++) {
                points.push(XB.transformToXY(data['points'][i]));
            }

            var line = new OpenLayers.Geometry.LineString(points);
            //var center = line.getCentroid();
            var bounds = line.getBounds();
            var feature = new OpenLayers.Feature.Vector(line, {}, { strokeColor: '#FF0000', strokeWidth: 4, strokeOpacity: 1.0});
            feature.state = OpenLayers.State.INSERT;
            features.push(feature);
            app.mapPanel.map.setCenter(
                    bounds.getCenterLonLat(),
                    Math.min(15, relativeZoom + app.mapPanel.map.getZoomForExtent(bounds, false))
            );
            XB.polygonLayer.addFeatures(features);
            XB.polygonLayer.redraw();
            if (duration != undefined && duration > 0) {
                setTimeout(function () {
                    XB.polygonLayer.removeFeatures(features);
                    XB.polygonLayer.redraw();
                }, duration);
            }
        }

    });

    console.log("sending portalReady to master from embed.html at end of app.on('ready') processing");
    XB.MESSAGING.getInstance().send(new Message("portalReady", {}));

    var legendInfo = [];
    for (var i = 0; i < app.mapPanel.map.layers.length; i++) {
        var layer = app.mapPanel.map.layers[i];
        legendInfo.push(
                {
                    name: layer.name,
                    id: layer.id,
                    visibility: layer.visibility,
                    opacity: layer.opacity,
                    legendData: XB.getLayerLegendInfo(app.config.map.layers, layer)
                }
        );
    }
    XB.MESSAGING.getInstance().send(new Message("postLegends", legendInfo));

    //**************************************** END - XBLOCK RELATED CODE ****************************************
};