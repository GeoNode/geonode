/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var {
    EDIT_MAP, editMap,
    UPDATE_CURRENT_MAP, updateCurrentMap,
    ERROR_CURRENT_MAP, errorCurrentMap
} = require('../currentMap');


describe('Test correctness of the maps actions', () => {

    it('editMap', () => {
        let thumbnail = "myThumnbnailUrl";
        let map = {
            thumbnail: thumbnail,
            id: 123,
            canWrite: true
        };
        var retval = editMap(map);
        expect(retval).toExist();
        expect(retval.type).toBe(EDIT_MAP);
        expect(retval.map.thumbnail).toBe(thumbnail);
        expect(retval.map.id).toBe(123);
        expect(retval.map.canWrite).toBeTruthy();
    });

    it('updateCurrentMap', () => {
        let files = [];
        let thumbnail = "myThumnbnailUrl";
        var retval = updateCurrentMap(files, thumbnail);
        expect(retval).toExist();
        expect(retval.type).toBe(UPDATE_CURRENT_MAP);
        expect(retval.thumbnail).toBe(thumbnail);
    });

    it('errorCurrentMap', () => {
        let errors = ["FORMAT"];
        var retval = errorCurrentMap(errors);
        expect(retval).toExist();
        expect(retval.type).toBe(ERROR_CURRENT_MAP);
        expect(retval.errors).toBe(errors);
    });

});
