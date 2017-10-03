ol.format.Style = function (opt_options) {

};

ol.format.Style.prototype.getGeometry = function(source) {

};

ol.format.Style.prototype.getFill = function (source) {

};

ol.format.Style.prototype.getImage = function (source) {

};

ol.format.Style.prototype.getStroke = function (source) {

};

ol.format.Style.prototype.getText = function (source) {

};

ol.format.Style.prototype.getZIndex = function (source) {

};

ol.format.Style.prototype.getStyle = function (source, zIndex) {
    var fill = new ol.style.Fill({
        color: new RGBColor(source['fillColor']).toRGBArray(source['fillOpacity'])
    });
    var stroke = new ol.style.Stroke({
        color: new RGBColor(source['strokeColor']).toRGBArray(1),
        width: parseFloat(source['strokeWidth'])
    });
    var image;
    if (source['externalGraphic']) {
        image = new ol.style.Icon({
            src: source['externalGraphic']
        });
    } else {
        image = new ol.style.Circle({
            fill: fill,
            stroke: stroke,
            radius: parseFloat(source['pointRadius'])
        });
    }
    return new ol.style.Style({
        fill: fill,
        stroke: stroke,
        image: image,
        text: new ol.style.Text({
            fill: new ol.style.Fill({
                color: source['fontColor']
            })
        }),
        zIndex: zIndex
    });
};