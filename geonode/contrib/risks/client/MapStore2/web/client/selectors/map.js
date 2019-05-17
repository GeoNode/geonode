/**
* Copyright 2016, GeoSolutions Sas.
* All rights reserved.
*
* This source code is licensed under the BSD-style license found in the
* LICENSE file in the root directory of this source tree.
*/

const CoordinatesUtils = require('../utils/CoordinatesUtils');
const MapUtils = require('../utils/MapUtils');
const {createSelector} = require('reselect');

const mapSelector = (state) => (state.map && state.map.present) || (state.map) || (state.config && state.config.map) || null;

const projectionSelector = createSelector([mapSelector], (map) => map && map.projection);


const scalesSelector = createSelector(
    [projectionSelector],
    (projection) => {
        if (projection) {
            const resolutions = MapUtils.getResolutions();
            const units = CoordinatesUtils.getUnits(projection);
            const dpm = 96 * (100 / 2.54);
            return resolutions.map((resolution) => resolution * dpm * (units === 'degrees' ? 111194.87428468118 : 1));
        }
        return [];
    }
);

module.exports = {
    mapSelector,
    scalesSelector
};
