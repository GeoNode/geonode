/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var Layers = require('../../../../utils/leaflet/Layers');
var L = require('leaflet');

var defaultStyle = {
    radius: 5,
    color: "red",
    weight: 1,
    opacity: 1,
    fillOpacity: 0
};

const assign = require('object-assign');

var createVectorLayer = function(options) {
    const {hideLoading} = options;
    const layer = L.geoJson([]/* options.features */, {
        pointToLayer: options.styleName !== "marker" ? function(feature, latlng) {
            return L.circleMarker(latlng, options.style || defaultStyle);
        } : null,
        hideLoading: hideLoading,
        style: options.nativeStyle || options.style || defaultStyle
    });
    layer.setOpacity = (opacity) => {
        const style = assign({}, layer.options.style || defaultStyle, {opacity: opacity, fillOpacity: opacity});
        layer.setStyle(style);
    };
    return layer;
};

Layers.registerType('vector', {
    create: (options) => {
        return createVectorLayer(options);
    },
    render: () => {
        return null;
    }
});
