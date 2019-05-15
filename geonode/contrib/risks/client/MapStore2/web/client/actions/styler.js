/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const STYLE_SAVED = 'STYLER_STYLE_SAVED';
const SET_STYLER_LAYER = 'SET_STYLER_LAYER';
const STYLE_SAVE_ERROR = 'STYLE_SAVE_ERROR';
const STYLER_RESET = 'STYLER_RESET';

const {getLayer} = require('../api/geoserver/Layers');
const {saveStyle} = require('../api/geoserver/Styles');

function setStylerLayer(layer) {
    return {
        type: SET_STYLER_LAYER,
        layer
    };
}
function styleSaved(name, style) {
    return {
        type: STYLE_SAVED,
        name,
        style
    };
}
function styleSaveError(layer, style, error) {
    return {
       type: STYLE_SAVE_ERROR,
       layer,
       style,
       error
   };
}
function reset(layer) {
    return {
        type: STYLER_RESET,
        layer
    };
}
function saveLayerDefaultStyle(geoserverBaseUrl, layerName, style) {
    return (dispatch) => {
        return getLayer(geoserverBaseUrl, layerName).then((layer) => {
            saveStyle(geoserverBaseUrl, layer.defaultStyle && layer.defaultStyle.name, style).then(()=> {
                dispatch(styleSaved(layer.defaultStyle.name, style));
            }).catch((e) => {styleSaveError(layerName, layer.defaultStyle, e); });

        }).catch((e) => {styleSaveError(layerName, null, e); });

    };
}
module.exports = {
    STYLE_SAVED,
    STYLER_RESET,
    SET_STYLER_LAYER,
    saveLayerDefaultStyle,
    setStylerLayer,
    reset
};
