/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');
var featuregrid = require('../featuregrid');

describe('Test the featuregrid reducer', () => {

    it('returns original state on unrecognized action', () => {
        let state = featuregrid(1, {type: 'UNKNOWN'});
        expect(state).toBe(1);
    });

    it('FeatureGrid selectFeature', () => {
        let testAction = {
            type: 'SELECT_FEATURES',
            features: [1, 2]
        };
        let state = featuregrid( {}, testAction);
        expect(state.select).toExist();
        expect(state.select[0]).toBe(1);
    });

});
