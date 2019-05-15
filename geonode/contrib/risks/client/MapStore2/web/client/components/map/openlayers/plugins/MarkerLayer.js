/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var Layers = require('../../../../utils/openlayers/Layers');
var ol = require('openlayers');
var assign = require('object-assign');
var defaultIcon = require('../img/marker-icon.png');

var icon = new ol.style.Style({
  image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
    anchor: [0.5, 1],
    anchorXUnits: 'fraction',
    anchorYUnits: 'fraction',
    opacity: 1,
    src: defaultIcon
  }))
});

const defaultStyles = {
  'Point': [new ol.style.Style({
    image: icon
  })]};


Layers.registerType('marker', {
    create: (options, map, mapId) => {
        return Layers.createLayer('vector', assign(options, {style: () => { return defaultStyles.Point; }}), map, mapId);

    }
});
