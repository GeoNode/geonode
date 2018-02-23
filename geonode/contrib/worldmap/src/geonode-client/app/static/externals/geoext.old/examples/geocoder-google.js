/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[geocoder-google]
 *  GeocoderComboBox Google
 *  -------------------------
 *  MapPanel with a Google Geocoder search field.
 */

var mapPanel;

Ext.onReady(function() {
    var geocoder = new google.maps.Geocoder();
    var locationLayer = new OpenLayers.Layer.Vector("Location", {
        styleMap: new OpenLayers.Style({
            externalGraphic: "http://openlayers.org/api/img/marker.png",
            graphicYOffset: -25,
            graphicHeight: 25,
            graphicTitle: "${formatted_address}"
        })
    });
    mapPanel = new GeoExt.MapPanel({
        renderTo: "mappanel",
        height: 400,
        width: 500,
        layers: [
            new OpenLayers.Layer.Google("Google", {numZoomLevels: 20}),
            locationLayer
        ],
        zoom: 1,
        tbar: [{
            xtype: "gx_geocodercombo",
            width: 250,
            layer: locationLayer,
            displayField: "formatted_address",
            store: new Ext.data.JsonStore({
                root: null,
                fields: [
                    "formatted_address",
                    {name: "lonlat", convert: function(v, rec) {
                        var latLng = rec.geometry.location;
                        return [latLng.lng(), latLng.lat()];
                    }},
                    {name: "bounds", convert: function(v, rec) {
                        var ne = rec.geometry.viewport.getNorthEast(),
                            sw = rec.geometry.viewport.getSouthWest();
                        return [sw.lng(), sw.lat(), ne.lng(), ne.lat()];
                    }}
                ],
                proxy: new (Ext.extend(Ext.data.DataProxy, {
                    doRequest: function(action, rs, params, reader, callback, scope, options) {
                        // To restrict the search to a bounding box, change the
                        // 1st argument of the geocoder.geocode call below to
                        // something like
                        // {address: params.q, bounds: new google.maps.LatLngBounds(
                        //     new google.maps.LatLng(47, 15),
                        //     new google.maps.LatLng(49, 17)
                        // )}
                        geocoder.geocode({address: params.q}, function(results, status) {
                            var readerResult = reader.readRecords(results);
                            callback.call(scope, readerResult, options, !!readerResult);                        
                        });
                    }
                }))({api: {read: true}})
            })
        }]
    });
});
