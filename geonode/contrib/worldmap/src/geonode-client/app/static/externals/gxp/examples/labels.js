var format = new OpenLayers.Format.SLD.v1_0_0_GeoServer();
var sldWin;
function showSLD(panel) {
    var symbolizer = panel.symbolizer;
    var node = format.writeNode("sld:TextSymbolizer", symbolizer);
    var text = OpenLayers.Format.XML.prototype.write.apply(format, [node]);
    if(!sldWin) {
        sldWin = new Ext.Window({
            title: "SLD",
            layout: "fit",
            closeAction: "hide",
            height: 300,
            width: 450,
            plain: true,
            modal: true,
            items: [{
                xtype: "textarea",
                value: text
            }]
        });
    } else {
        sldWin.items.items[0].setValue(text);
    }
    sldWin.show();
}

function applySLD(symbolizer, layer) {
    var format = new OpenLayers.Format.SLD({
        multipleSymbolizers: true,
        profile: 'GeoServer',
        namedLayersAsArray: true
    });
    symbolizer = new OpenLayers.Symbolizer.Text(symbolizer);
    var polygonSymbolizer = new OpenLayers.Symbolizer.Polygon({fillOpacity: 0});
    var pointSymbolizer = new OpenLayers.Symbolizer.Point({fill: true, fillColor: '#FF0000', pointRadius: 3, graphicName: 'circle'});
    var sldConfig = {
        namedLayers: [{
            name: 'usa:states',
            userStyles: [new OpenLayers.Style2({rules: [new OpenLayers.Rule({
                symbolizers: [symbolizer, polygonSymbolizer, pointSymbolizer]})
            ]})]
        }]
    };
    var sld = format.write(sldConfig);
    layer.setVisibility(true);
    layer.mergeNewParams({SLD_BODY: sld, "_olSalt": Math.random()});
}

Ext.onReady(function() {
    Ext.QuickTips.init();
    var map = new OpenLayers.Map('map', {allOverlays: true});
    var layer = new OpenLayers.Layer.WMS("usa states", "http://suite.opengeo.org/geoserver/wms?", 
        {
            layers: 'usa:states',
            format: 'image/png',
            transparent: 'TRUE'
        }, {
            singleTile: true,
            visibility: false
        }
    );
    map.addLayers([layer]);
    map.setCenter([-100, 38], 4);

    var panel = new gxp.TextSymbolizer({
        title: "Text Symbolizer",
        renderTo: "panel",
        width: 250,
        border: true,
        bodyStyle: {padding: 10},
        attributes: new GeoExt.data.AttributeStore({
            url: "data/describe_feature_type.xml",
            ignore: {name: "the_geom"}
        }),
        tbar: ["->", {
            text: "Show SLD",
            handler: function() {
                showSLD(panel);
            }
        }, {
            text: "Apply SLD",
            handler: function() {
                applySLD(panel.symbolizer, layer);
            }
        }]
    });

});
