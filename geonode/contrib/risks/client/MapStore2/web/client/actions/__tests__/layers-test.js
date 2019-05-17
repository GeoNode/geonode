/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var expect = require('expect');
var {
    TOGGLE_NODE,
    SORT_NODE,
    REMOVE_NODE,
    UPDATE_NODE,
    CHANGE_LAYER_PROPERTIES,
    LAYER_LOADING,
    LAYER_LOAD,
    LAYER_ERROR,
    ADD_LAYER,
    REMOVE_LAYER,
    SHOW_SETTINGS,
    HIDE_SETTINGS,
    UPDATE_SETTINGS,
    changeLayerProperties,
    toggleNode,
    sortNode,
    removeNode,
    updateNode,
    layerLoading,
    layerLoad,
    layerError,
    addLayer,
    removeLayer,
    showSettings,
    hideSettings,
    updateSettings
} = require('../layers');
var {getLayerCapabilities} = require('../layerCapabilities');

describe('Test correctness of the layers actions', () => {
    it('test layer properties change action', (done) => {
        let e = changeLayerProperties('layer', {visibility: true});

        try {
            expect(e).toExist();
            expect(e.type).toBe(CHANGE_LAYER_PROPERTIES);
            expect(e.newProperties).toExist();
            expect(e.newProperties.visibility).toBe(true);
            expect(e.layer).toBe('layer');
            done();
        } catch(ex) {
            done(ex);
        }

    });

    it('sortNode', () => {
        const order = [0, 2, 1];

        var retval = sortNode('group', order);

        expect(retval).toExist();
        expect(retval.type).toBe(SORT_NODE);
        expect(retval.node).toBe('group');
        expect(retval.order).toBe(order);
    });

    it('toggleNode', () => {
        var retval = toggleNode('sample', 'groups', true);

        expect(retval).toExist();
        expect(retval.type).toBe(TOGGLE_NODE);
        expect(retval.node).toBe('sample');
        expect(retval.nodeType).toBe('groups');
        expect(retval.status).toBe(false);
    });

    it('removeNode', () => {
        var retval = removeNode('sampleNode', 'sampleType');

        expect(retval).toExist();
        expect(retval.type).toBe(REMOVE_NODE);
        expect(retval.node).toBe('sampleNode');
        expect(retval.nodeType).toBe('sampleType');
    });

    it('updateNode', () => {
        var retval = updateNode('sampleNode', 'sampleType', 'sampleOptions');

        expect(retval).toExist();
        expect(retval.type).toBe(UPDATE_NODE);
        expect(retval.node).toBe('sampleNode');
        expect(retval.nodeType).toBe('sampleType');
        expect(retval.options).toBe('sampleOptions');
    });

    it('a layer is loading', () => {
        const testVal = 'layer1';
        const retval = layerLoading(testVal);

        expect(retval).toExist();
        expect(retval.type).toBe(LAYER_LOADING);
        expect(retval.layerId).toBe(testVal);
    });

    it('a layer is load', () => {
        const testVal = 'layer1';
        const retval = layerLoad(testVal);

        expect(retval).toExist();
        expect(retval.type).toBe(LAYER_LOAD);
        expect(retval.layerId).toBe(testVal);
    });

    it('a layer is not loaded with errors', () => {
        const testVal = 'layer1';
        const retval = layerError(testVal);

        expect(retval).toExist();
        expect(retval.type).toBe(LAYER_ERROR);
        expect(retval.layerId).toBe(testVal);
    });

    it('add layer', () => {
        const testVal = 'layer1';
        const retval1 = addLayer(testVal);

        expect(retval1).toExist();
        expect(retval1.type).toBe(ADD_LAYER);
        expect(retval1.layer).toBe(testVal);
        expect(retval1.foreground).toBe(true);

        const retval2 = addLayer(testVal, true);

        expect(retval2).toExist();
        expect(retval2.type).toBe(ADD_LAYER);
        expect(retval2.layer).toBe(testVal);
        expect(retval2.foreground).toBe(true);
    });

    it('remove layer', () => {
        const testVal = 'layerid1';
        const retval = removeLayer(testVal);

        expect(retval).toExist();
        expect(retval.type).toBe(REMOVE_LAYER);
        expect(retval.layerId).toBe(testVal);
    });

    it('show settings', () => {
        const action = showSettings("node1", "layers", {opacity: 0.5});
        expect(action).toExist();
        expect(action.type).toBe(SHOW_SETTINGS);
        expect(action.node).toBe("node1");
        expect(action.nodeType).toBe("layers");
        expect(action.options).toEqual({opacity: 0.5});
    });

    it('hide settings', () => {
        const action = hideSettings();
        expect(action).toExist();
        expect(action.type).toBe(HIDE_SETTINGS);
    });

    it('update settings', () => {
        const action = updateSettings({opacity: 0.5, size: 500});
        expect(action).toExist();
        expect(action.type).toBe(UPDATE_SETTINGS);
        expect(action.options).toEqual({opacity: 0.5, size: 500});
    });
    it('get layer capabilities', (done) => {
        const layer = {
            id: "TEST_ID",
            name: 'testworkspace:testlayer',
            title: 'Layer',
            visibility: true,
            storeIndex: 9,
            type: 'shapefile',
            url: 'base/web/client/test-resources/geoserver/wms'
        };
        const actionCall = getLayerCapabilities(layer);
        expect(actionCall).toExist();
        actionCall((action)=> {
            expect(action).toExist();
            expect(action.options).toExist();
            expect(action.type === UPDATE_NODE);
            if (action.options.capabilities) {
                done();
            }
        });
    });
});
