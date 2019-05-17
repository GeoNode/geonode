/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const assign = require('object-assign');
const ol = require('openlayers');

const getColor = function(color) {
        return `rgba(${ color.r }, ${ color.g }, ${ color.b }, ${ color.a })`;
    };
const getGeomType = function(layer) {
    return (layer.features && layer.features[0]) ? layer.features[0].geometry.type : undefined;
};
const toVectorStyle = function(layer, style) {
        let newLayer = assign({}, layer);
        let geomT = getGeomType(layer);
        if (style.marker && (geomT === 'Point' || geomT === 'MultiPoint')) {
            newLayer.styleName = "marker";
        }else {
            newLayer.style = {
                weight: style.width,
                radius: style.radius,
                opacity: style.color.a,
                fillOpacity: style.fill.a,
                color: getColor(style.color),
                fillColor: getColor(style.fill)
            };
            let stroke = new ol.style.Stroke({
                            color: getColor(style.color),
                            width: style.width
                        });
            let fill = new ol.style.Fill({
                            color: getColor(style.fill)
                        });
            switch (getGeomType(layer)) {
                case 'Polygon':
                case 'MultiPolygon': {
                    newLayer.nativeStyle = new ol.style.Style({
                        stroke: stroke,
                        fill: fill
                    });
                    break;
                }
                case 'MultiLineString':
                case 'LineString':
                {
                    newLayer.nativeStyle = new ol.style.Style({
                        stroke: stroke
                    });
                    break;
                }
                case 'Point':
                case 'MultiPoint': {
                    newLayer.nativeStyle = new ol.style.Style({
                        image: new ol.style.Circle({
                            radius: style.radius,
                            fill: fill,
                            stroke: stroke
                            })});
                    break;
                }
                default: {
                    newLayer.style = null;
                }
            }
        }
        return newLayer;
    };

module.exports = toVectorStyle;
