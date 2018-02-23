var mapPanel;

Ext.onReady(function() {
    
    var map = new OpenLayers.Map({
        theme: null,
        allOverlays: true
    });    

    var imagery = new OpenLayers.Layer.WMS(
        "Global Imagery",
        "http://demo.opengeo.org/geoserver/wms",
        {layers: "bluemarble"}
    );
    map.addLayer(imagery);

    var imagery = new OpenLayers.Layer.WMS(
        "States",
        "http://demo.opengeo.org/geoserver/wms",
        {layers: "topp:states", transparent: "TRUE"}
    );
    map.addLayer(imagery);
    
    var layerStore = new GeoExt.data.LayerStore({
        map: map,
        layers: map.layers
    });

    mapPanel = new GeoExt.MapPanel({
        renderTo: "mappanel",
        height: 400,
        width: 600,
        map: map,
        center: [-100, 39],
        zoom: 3,
        tbar: ["->", {
            text: "Layer Switcher",
            menu: new gxp.menu.LayerMenu({
                layers: layerStore
            })
        }]
    });

});



