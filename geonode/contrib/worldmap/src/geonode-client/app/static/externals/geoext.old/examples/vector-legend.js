/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[vector-legend]
 *  Vector Legend
 *  -------------------------
 *  Render a legend for a vector layer.
 */

var mapPanel, legendPanel;

Ext.onReady(function() {

    var rules = [
        new OpenLayers.Rule({
            title: "> 2000m",
            maxScaleDenominator: 3000000,
            filter: new OpenLayers.Filter.Comparison({
                type: OpenLayers.Filter.Comparison.GREATER_THAN,
                property: "elevation",
                value: 2000
            }),
            symbolizer: {
                graphicName: "star",
                pointRadius: 8,
                fillColor: "#99ccff",
                strokeColor: "#666666",
                strokeWidth: 1
            }
        }),
        new OpenLayers.Rule({
            title: "1500 - 2000m",
            maxScaleDenominator: 3000000,
            filter: new OpenLayers.Filter.Comparison({
                type: OpenLayers.Filter.Comparison.BETWEEN,
                property: "elevation",
                upperBoundary: 2000,
                lowerBoundary: 1500
            }),
            symbolizer: {
                graphicName: "star",
                pointRadius: 6,
                fillColor: "#6699cc",
                strokeColor: "#666666",
                strokeWidth: 1
            }
        }),
        new OpenLayers.Rule({
            title: "< 1500m",
            maxScaleDenominator: 3000000,
            filter: new OpenLayers.Filter.Comparison({
                type: OpenLayers.Filter.Comparison.LESS_THAN,
                property: "elevation",
                value: 1500
            }),
            symbolizer: {
                graphicName: "star",
                pointRadius: 4,
                fillColor: "#0033cc",
                strokeColor: "#666666",
                strokeWidth: 1
            }
        }),
        new OpenLayers.Rule({
            title: "All",
            minScaleDenominator: 3000000,
            symbolizer: {
                graphicName: "star",
                pointRadius: 5,
                fillColor: "#99ccff",
                strokeColor: "#666666",
                strokeWidth: 1
            }
        })
    ];

    var imagery = new OpenLayers.Layer.WMS(
        "Imagery",
        "http://maps.opengeo.org/geowebcache/service/wms",
        {layers: "bluemarble"},
        {displayInLayerSwitcher: false}
    );

    var summits = new OpenLayers.Layer.Vector("Summits", {
        strategies: [new OpenLayers.Strategy.Fixed()],
        protocol: new OpenLayers.Protocol.HTTP({
            url: "data/summits.json",
            format: new OpenLayers.Format.GeoJSON()
        }),
        styleMap: new OpenLayers.StyleMap(new OpenLayers.Style({}, {rules: rules}))
    });
    
    mapPanel = new GeoExt.MapPanel({
        renderTo: "mappanel",
        border: false,
        layers: [imagery, summits],
        center: [6.3, 45.6],
        height: 256, // IE6 wants this
        zoom: 8
    });
    
    legendPanel = new GeoExt.LegendPanel({
        layerStore: mapPanel.layers,
        renderTo: "legend",
        border: false
    });

});
