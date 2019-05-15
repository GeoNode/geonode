/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');
var snapshot = require('../snapshot');
var {CHANGE_SNAPSHOT_STATE, SNAPSHOT_READY, SNAPSHOT_ERROR, SNAPSHOT_ADD_QUEUE, SNAPSHOT_REMOVE_QUEUE} = require('../../actions/snapshot');

describe('Test the snapshot reducer', () => {

    it('snapshot state', () => {
        let state = snapshot({}, {type: CHANGE_SNAPSHOT_STATE, state: "DISABLED"});
        expect(state).toExist();
        expect(state.state).toBe("DISABLED");
        state = snapshot({}, {type: CHANGE_SNAPSHOT_STATE, state: "SHOTING"});
        expect(state).toExist();
        expect(state.state).toBe("SHOTING");
        state = snapshot({}, {type: CHANGE_SNAPSHOT_STATE, state: "READY"});
        expect(state).toExist();
        expect(state.state).toBe("READY");
    });
    it('snapshot ready', () => {
        let state = snapshot({}, {type: SNAPSHOT_READY, imgData: "snapshot", width: 20, height: 20, size: 20});
        expect(state).toExist();
        expect(state.img).toExist();
        expect(state.img.data).toBe("snapshot");
        expect(state.img.width).toBe(20);
        expect(state.img.height).toBe(20);
        expect(state.img.size).toBe(20);
    });
    it('snapshot error', () => {
        let state = snapshot({}, {type: SNAPSHOT_ERROR, error: "snapshot error"});
        expect(state).toExist();
        expect(state.error).toBe("snapshot error");
    });
    it('snapshot queue add', () => {
        let state = snapshot({}, {type: SNAPSHOT_ADD_QUEUE, options: {test: "test1"}});
        expect(state).toExist();
        expect(state.queue).toExist();
        expect(state.queue.length).toBe(1);
    });
    it('snapshot queue remove', () => {
        let state = snapshot({queue: [{key: 1}, {key: 2}]}, {type: SNAPSHOT_REMOVE_QUEUE, options: {key: 1}});
        expect(state).toExist();
        expect(state.queue).toExist();
        expect(state.queue.length).toBe(1);
    });

});
