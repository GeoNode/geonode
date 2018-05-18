var map = new OpenLayers.Map({
    div: "map",
    theme: null,
    layers: [new OpenLayers.Layer.OSM()],
    center: new OpenLayers.LonLat(-8237542, 4970279),
    zoom: 12
});

var gg = new OpenLayers.Projection("EPSG:4326");
var sm = map.getProjectionObject();
var listeners = {
    select: function(combo, record) {
        var bounds = record.get("viewport").transform(gg, sm);
        map.zoomToExtent(bounds, true);
    }
};

var combo1 = new gxp.form.GoogleGeocoderComboBox({
    renderTo: "combo1",
    width: 200,
    listeners: listeners
});

var combo2 = new gxp.form.GoogleGeocoderComboBox({
    renderTo: "combo2",
    bounds: new OpenLayers.Bounds(-74.04167, 40.69547, -73.86589, 40.87743),
    width: 200,
    listeners: listeners
});
