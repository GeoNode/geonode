/**
* Copyright 2016, GeoSolutions Sas.
* All rights reserved.
*
* This source code is licensed under the BSD-style license found in the
* LICENSE file in the root directory of this source tree.
*/

const expect = require('expect');
const {mapSelector} = require('../map');

describe('Test map selectors', () => {
    it('test mapSelector from config', () => {
        const props = mapSelector({config: {map: {center: {x: 1, y: 1}}}});

        expect(props.center).toExist();
        expect(props.center.x).toBe(1);
    });

    it('test mapSelector from map', () => {
        const props = mapSelector({map: {center: {x: 1, y: 1}}});

        expect(props.center).toExist();
        expect(props.center.x).toBe(1);
    });

    it('test mapSelector from map with history', () => {
        const props = mapSelector({map: {present: {center: {x: 1, y: 1}}}});

        expect(props.center).toExist();
        expect(props.center.x).toBe(1);
    });

    it('test mapSelector from map non configured', () => {
        const props = mapSelector({config: null});

        expect(props).toNotExist();
    });
});
