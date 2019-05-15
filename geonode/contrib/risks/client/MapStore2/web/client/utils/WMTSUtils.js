/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */


const CoordinatesUtils = require('./CoordinatesUtils');
const {isString, isArray, isObject, head} = require('lodash');

const WMTSUtils = {
    getTileMatrixSet: (tileMatrixSet, srs, allowedSRS) => {
        if (tileMatrixSet && isString(tileMatrixSet)) {
            return tileMatrixSet;
        }
        if (tileMatrixSet) {
            return CoordinatesUtils.getEquivalentSRS(srs, allowedSRS).reduce((previous, current) => {
                if (isArray(tileMatrixSet)) {
                    const matching = head(tileMatrixSet.filter((matrix) => (matrix["ows:Identifier"] === current || CoordinatesUtils.getEPSGCode(matrix["ows:SupportedCRS"]) === current)));
                    return matching && matching["ows:Identifier"] || previous;
                } else if (isObject(tileMatrixSet)) {
                    return tileMatrixSet[current] || previous;
                }
                return previous;
            }, srs);
        }
        if (tileMatrixSet && isArray(tileMatrixSet)) {
            return CoordinatesUtils.getEquivalentSRS(srs, allowedSRS).reduce((previous, current) => {
                return tileMatrixSet[current] || previous;
            }, srs);
        }
        return srs;
    }
};


module.exports = WMTSUtils;
