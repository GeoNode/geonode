/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const {connect} = require('react-redux');
const {createSelector} = require('reselect');
const {layersSelector} = require('../selectors/layers');

const assign = require('object-assign');

const selector = createSelector([layersSelector], (layers) => ({
    loading: layers && layers.some((layer) => layer.loading)
}));

require('./maploading/maploading.css');

const MapLoadingPlugin = connect(selector)(require('../components/misc/spinners/GlobalSpinner/GlobalSpinner'));

module.exports = {
    MapLoadingPlugin: assign(MapLoadingPlugin, {
        Toolbar: {
            name: 'maploading',
            position: 1,
            tool: true,
            priority: 1
        }
    }),
    reducers: {}
};
