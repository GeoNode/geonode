Ext.onReady(function() {
    var win, block = Ext.Element.get(Ext.DomQuery.select("div.execute")[0]);
    var button = new Ext.Button({
        text: "Run it!",
        cls: "execute",
        handler: function() {
            if(!win) {
                win = new Ext.Window({
                    title: "GeoExt in Action",
                    height: 280, width: 450,
                    layout: "fit",
                    closeAction: "hide",
                    items: [{
                        xtype: "gx_mappanel",
                        layers: [new OpenLayers.Layer.WMS(
                            "Global Imagery", "http://demo.opengeo.org/geoserver/wms",
                            {layers: 'bluemarble'}
                        )],
                        zoom: 1
                    }]
                });
            }
            win.show(container);
        }
    });
    var container = Ext.Element.get(Ext.DomHelper.append(block, {tag: "div"}));
    container.setHeight(35, {callback: function() {button.render(container)}});
});