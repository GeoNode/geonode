/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const assign = require('object-assign');

const getColor = function(color) {
        return `rgb(${ color.r }, ${ color.g }, ${ color.b })`;
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
        }
        return newLayer;
    };

module.exports = toVectorStyle;
