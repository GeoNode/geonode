var sldWin, grid, symbolizers = [];
symbolizers.push(new OpenLayers.Symbolizer.Point({
    graphicName: "star",
    pointRadius: 8,
    fillColor: "yellow",
    strokeColor: "red",
    strokeWidth: 1
}));
symbolizers.push(new OpenLayers.Symbolizer.Line({
    strokeColor: "#669900",
    strokeWidth: 3
}));
symbolizers.push(new OpenLayers.Symbolizer.Polygon({
    fillColor: "olive",
    fillOpacity: 0.25,
    strokeColor: "#666666",
    strokeWidth: 2,
    strokeDashstyle: "dot"
}));
symbolizers.push(new OpenLayers.Symbolizer.Text({
    label: "${name}",
    labelAlign: "cm",
    fontColor: "#FF0000",
    fillColor: "yellow",
    graphicName: "square",
    pointRadius: 10
}));

var showSLD = function() {
    var format = new OpenLayers.Format.SLD({
        multipleSymbolizers: true,
        profile: 'GeoServer',
        namedLayersAsArray: true
    });
    var sldConfig = {
        namedLayers: [{
            name: 'foo',
            userStyles: [new OpenLayers.Style2({rules: [new OpenLayers.Rule({
                symbolizers: grid.getSymbolizers()})
            ]})]
        }]
    };
    var sld = format.write(sldConfig);
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
                value: sld
            }]
        });
    } else {
        sldWin.items.items[0].setValue(sld);
    }
    sldWin.show();
};

Ext.onReady(function() {
    grid = new gxp.grid.SymbolizerGrid({
        symbolizers: symbolizers,
        height: 375,
        width: 400,
        renderTo: "grid",
        tbar: [{
            text: 'Show SLD',
            handler: showSLD
        }]
    });
});
