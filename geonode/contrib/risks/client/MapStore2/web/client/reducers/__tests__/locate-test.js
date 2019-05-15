/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');
var locate = require('../locate');

describe('Test the locate reducer', () => {

    it('locate state', () => {
        let state = locate({}, {type: 'CHANGE_LOCATE_STATE', state: "ENABLED"});
        expect(state).toExist();
        expect(state.state).toBe("ENABLED");
        state = locate({}, {type: 'CHANGE_LOCATE_STATE', state: "DISABLED"});
        expect(state).toExist();
        expect(state.state).toBe("DISABLED");
        state = locate({}, {type: 'CHANGE_LOCATE_STATE', state: "FOLLOWING"});
        expect(state).toExist();
        expect(state.state).toBe("FOLLOWING");
        state = locate({}, {type: 'CHANGE_LOCATE_STATE', state: "LOCATING"});
        expect(state).toExist();
        expect(state.state).toBe("LOCATING");
    });

});
