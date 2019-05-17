/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var {
    THEME_SELECTED,
    selectTheme
} = require('../theme');

describe('Test theme related actions', () => {
    it('test theme selection action', () => {
        let theme = {id: "newtheme"};
        let e = selectTheme(theme);

        expect(e).toExist();
        expect(e.type).toBe(THEME_SELECTED);
        expect(e.theme).toExist();
        expect(e.theme).toBe(theme);

    });
});
