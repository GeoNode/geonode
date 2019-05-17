
/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const expect = require('expect');

const theme = require('../theme');
const {selectTheme} = require('../../actions/theme');


describe('Test the theme reducer', () => {
    it('should maange the THEME_SELECTED action', () => {
        var state = theme({}, selectTheme({id: "default"}));
        expect(state.selectedTheme).toExist();
        expect(state.selectedTheme.id).toBe("default");
    });

});
