/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const {
    SELECT_FEATURES,
    selectFeatures
} = require('../featuregrid');

describe('Test correctness of featurgrid actions', () => {

    it('Test selectFeature action creator', () => {
        const features = [1, 2];

        const retval = selectFeatures(features);

        expect(retval).toExist();
        expect(retval.type).toBe(SELECT_FEATURES);
        expect(retval.features).toExist();
        expect(retval.features).toBe(features);
    });

});
