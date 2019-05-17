/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');

var browser = require('../browser');
var ConfigUtils = require('../../utils/ConfigUtils');

describe('Test the browser reducer', () => {
    it('Get borwser properties', () => {
        var state = browser({}, {type: 'CHANGE_BROWSER_PROPERTIES', newProperties: ConfigUtils.getBrowserProperties()});
        expect(state.hasOwnProperty('touch')).toBe(true);
        expect(state.hasOwnProperty('mobile')).toBe(true);
    });

});
