/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[geocoder-geonames]
 *  GeocoderComboBox GeoNames
 *  -------------------------
 *  MapPanel with a GeoNames search field.
 */

var mapPanel;

Ext.onReady(function() {
    mapPanel = new GeoExt.MapPanel({
        renderTo: "mappanel",
        height: 400,
        width: 500,
        layers: [new OpenLayers.Layer.OSM()],
        zoom: 1,
        tbar: [{
            xtype: "gx_geocodercombo",
            emptyText: "Search GeoNames",
            width: 300,
            tpl: '<tpl for="."><div class="x-combo-list-item">[{countryName}] {name}</div></tpl>',
            valueField: "lonlat",
            store: new Ext.data.JsonStore({
                root: "geonames",
                fields: [
                    "name", "countryName",
                    {name: "lonlat", convert: function(v, rec) {
                        return [rec.lng, rec.lat];
                    }}
                ],
                proxy: new Ext.data.ScriptTagProxy({
                    url: "http://ws.geonames.org/searchJSON?maxRows=20"
                })
            })
        }]
    });
});

