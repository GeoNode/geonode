/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const {
    HIGHLIGHT_STATUS,
    UPDATE_HIGHLIGHTED,
    highlightStatus,
    updateHighlighted
} = require('../highlight');

describe('Test correctness of the highlight actions', () => {

    it('highlightStatus', () => {
        let status = "enabled";

        let retval = highlightStatus(status);

        expect(retval).toExist();
        expect(retval.type).toBe(HIGHLIGHT_STATUS);
        expect(retval.status).toBe("enabled");
    });

    it('updateHighlighted', () => {
        let features = ["One", "Two"];

        let retval = updateHighlighted(features, 'update');

        expect(retval).toExist();
        expect(retval.type).toBe(UPDATE_HIGHLIGHTED);
        expect(retval.features).toBe(features);
        expect(retval.status).toBe('update');

    });
});
