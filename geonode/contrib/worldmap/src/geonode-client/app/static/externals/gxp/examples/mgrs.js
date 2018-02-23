var panel = new GeoExt.MapPanel({
    renderTo: "panel",
    width: 450,
    height: 300,
    layers: [new OpenLayers.Layer.OSM()],
    map: {
        controls: [
            new OpenLayers.Control.PanPanel(),
            new OpenLayers.Control.ZoomPanel(),
            new OpenLayers.Control.Navigation(),
            new OpenLayers.Control.Attribution(),
            new OpenLayers.Control.MousePosition({
                formatOutput: function(lonlat) {
                    return MGRS.forward(lonlat, panel.accuracyField.getValue());
                }
            })
        ],
        displayProjection: "EPSG:4326"
    }, 
    extent: new OpenLayers.Bounds(-180, -90, 180, 90).transform("EPSG:4326", "EPSG:3857"),
    tbar: [{
        xtype: "textfield",
        emptyText: "Enter MGRS reference",
        ref: "../mgrsField"
    }, '->', "MGRS accuracy:", {
        xtype: "combo",
        ref: "../accuracyField",
        triggerAction: "all",
        store: [[1, "10000 m"], [2, "1000 m"], [3, "100 m"], [4, "10 m"], [5, "1 m"]],
        width: 70,
        value: 1
    }],
    keys: [{
        key: [Ext.EventObject.ENTER],
        handler: function() {
            if (Ext.EventObject.getTarget() === panel.mgrsField.getEl().dom) {
                var bbox = OpenLayers.Bounds.fromArray(
                    MGRS.inverse(panel.mgrsField.getValue())
                );
                panel.map.zoomToExtent(bbox.transform("EPSG:4326", "EPSG:3857"));
            }
        }
    }]
    
});