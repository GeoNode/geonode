/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[geocoder-wfs]
 *  GeocoderComboBox WFS
 *  -------------------------
 *  MapPanel with a WFS Geocoder search field.
 */

var mapPanel;

Ext.onReady(function() {
    mapPanel = new GeoExt.MapPanel({
        renderTo: "mappanel",
        height: 400,
        width: 500,
        layers: [
            new OpenLayers.Layer.OSM()
        ],
        center: [-10764594.758211, 4523072.3184791],
        zoom: 3,
        tbar: [{
            xtype: "gx_geocodercombo",
            srs: "EPSG:900913",
            emptyText: 'Search for a US state',
            queryParam: "CQL_FILTER",
            store: new Ext.data.Store({
                reader: new GeoExt.data.FeatureReader({}, [
                    {name: 'name', mapping: 'STATE_NAME'},
                    {name: 'bounds', convert: function(v, feature) {
                        return feature.geometry.getBounds().toArray();
                    }}
                ]),
                proxy: new GeoExt.data.ProtocolProxy({
                    protocol: new OpenLayers.Protocol.Script({
                        url: "http://demo.opengeo.org/geoserver/wfs",
                        callbackKey: "format_options",
                        callbackPrefix: "callback:",
                        params: {
                            service: "WFS",
                            version: "1.1.0",
                            srsName: "EPSG:900913",
                            request: "GetFeature",
                            typeName: "topp:states",
                            outputFormat: "json"
                        }
                    })
                })
            }),
            listeners: {
                beforequery: function(qe) {
                    qe.query = "STATE_NAME like '%" + qe.query + "%'";
                }
            }
        }]
    });
});

/**
 * The commented example below uses plain WFS but needs a proxy
 */
/*Ext.onReady(function() {
    mapPanel = new GeoExt.MapPanel({
        renderTo: "mappanel",
        height: 400,
        width: 500,
        layers: [
            new OpenLayers.Layer.OSM()
        ],
        center: [-10764594.758211, 4523072.3184791],
        zoom: 3,
        tbar: [{
            xtype: "gx_geocodercombo",
            srs: "EPSG:900913",
            width: 250,
            store: new Ext.data.Store({
                reader: new GeoExt.data.FeatureReader({}, [
                    {name: 'name', mapping: 'STATE_NAME'},
                    {name: 'bounds', convert: function(v, feature) {
                        return feature.geometry.getBounds().toArray();
                    }}
                ]),
                proxy: new (Ext.extend(GeoExt.data.ProtocolProxy, {
                    doRequest: function(action, records, params, reader, callback, scope, arg) {
                        if (params.q) {
                            params.filter = new OpenLayers.Filter.Comparison({
                                type: OpenLayers.Filter.Comparison.LIKE,
                                matchCase: false,
                                property: 'STATE_NAME',
                                value: '*' + params.q + '*'
                            });
                            delete params.q;
                        }
                        GeoExt.data.ProtocolProxy.prototype.doRequest.apply(this, arguments);
                    }
                }))({
                    protocol: new OpenLayers.Protocol.WFS({
                        version: "1.1.0",
                        url: "http://demo.opengeo.org/geoserver/wfs",
                        featureType: "states",
                        featurePrefix: "topp",
                        srsName: "EPSG:900913",
                        propertyNames: ['STATE_NAME', 'the_geom'],
                        maxFeatures: 20
                    }),
                    setParamsAsOptions: true
                })
            })
        }]
    });
});
*/
