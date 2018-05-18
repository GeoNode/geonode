/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

var filter = new OpenLayers.Filter.Comparison({
    type: OpenLayers.Filter.Comparison.EQUAL_TO,
    property: "STATE_NAME",
    value: "Montana"
});

var feWin = null;
var format = new OpenLayers.Format.Filter();
function showFE() {
    var node = format.write(filter);
    var text = OpenLayers.Format.XML.prototype.write.apply(format, [node]);
    if(!feWin) {
        feWin = new Ext.Window({
            title: "Filter Encoding",
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
        feWin.items.items[0].setValue(text);
    }
    feWin.show();
}

Ext.onReady(function() {

    Ext.QuickTips.init();
    var win = new Ext.Window({
        title: "Comparison Filter",
        closable: false,
        bodyStyle: {padding: 10},
        width: 370,
        layout: "form",
        hideLabels: true,
        items: [{
            xtype: "gxp_filterfield",
            anchor: "100%",
            filter: filter,
            attributes: new GeoExt.data.AttributeStore({
                url: "data/describe_feature_type.xml",
                ignore: {name: "the_geom"}
            })
        }],
        bbar: ["->", {
            text: "View Filter Encoding",
            handler: function() {
                showFE();
            }
        }]
    });
    win.show();

});
