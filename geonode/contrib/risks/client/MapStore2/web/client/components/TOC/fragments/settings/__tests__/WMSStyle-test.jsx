/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var ReactDOM = require('react-dom');
var ReactTestUtils = require('react-addons-test-utils');
var WMSStyle = require('../WMSStyle');

var expect = require('expect');

describe('test  Layer Properties General module component', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('tests component rendering', () => {
        const l = {
            name: 'testworkspace:testlayer',
            title: 'Layer',
            visibility: true,
            storeIndex: 9,
            type: 'shapefile',
            url: 'base/web/client/test-resources/geoserver/wms'
        };
        const settings = {
            options: {opacity: 1}
        };

        const comp = ReactDOM.render(<WMSStyle element={l} settings={settings} />, document.getElementById("container"));
        expect(comp).toExist();
        const form = ReactTestUtils.scryRenderedDOMComponentsWithTag( comp, "form" );
        expect(form).toExist();

    });
    it('tests component events', () => {
        const l = {
            name: 'testworkspace:testlayer',
            title: 'Layer',
            visibility: true,
            storeIndex: 9,
            type: 'wms',
            url: 'base/web/client/test-resources/geoserver/wms',
            availableStyles: [{name: 'style1'}]

        };
        const settings = {
            options: {opacity: 1}
        };
        const handlers = {
            retrieveLayerData: () => {},
            updateSettings: () => {}
        };
        let spyRetrive = expect.spyOn(handlers, "retrieveLayerData");
        let spyUpdate = expect.spyOn(handlers, "updateSettings");

        const comp = ReactDOM.render(<WMSStyle element={l} settings={settings} retrieveLayerData={handlers.retrieveLayerData} updateSettings={handlers.updateSettings}/>, document.getElementById("container"));
        expect(comp).toExist();
        // refresh layers list button click
        const buttons = ReactTestUtils.scryRenderedDOMComponentsWithTag( comp, "button" );
        expect(buttons).toExist();
        expect(buttons.length).toBe(1);
        ReactTestUtils.Simulate.click(buttons[0]);
        expect(spyRetrive.calls.length).toBe(1);

        // Simpulate selection
        const selectArrow = ReactDOM.findDOMNode(comp).querySelector('.Select-arrow');
        const selectControl = ReactDOM.findDOMNode(comp).querySelector('.Select-control');
        const inputs = ReactTestUtils.scryRenderedDOMComponentsWithTag( comp, "input" );
        ReactTestUtils.Simulate.mouseDown(selectArrow, { button: 0 });
        ReactTestUtils.Simulate.keyDown(selectControl, { keyCode: 40, key: 'ArrowDown' });
        ReactTestUtils.Simulate.keyDown(inputs[0], { keyCode: 13, key: 'Enter' });
        expect(spyUpdate.calls.length).toBe(1);

        // click on arrow of the select auto try to retrieve data if not present
        const l2 = {
            name: 'testworkspace:testlayer',
            title: 'Layer',
            visibility: true,
            storeIndex: 9,
            type: 'wms',
            url: 'base/web/client/test-resources/geoserver/wms'
        };
        const comp1 = ReactDOM.render(<WMSStyle element={l2} settings={settings} retrieveLayerData={handlers.retrieveLayerData} updateSettings={handlers.updateSettings}/>, document.getElementById("container"));
        const selectArrow1 = ReactDOM.findDOMNode(comp1).querySelector('.Select-arrow');
        ReactTestUtils.Simulate.click(selectArrow1);
        expect(spyRetrive.calls.length).toBe(2);
    });
    it('tests rendering error', () => {
        const l = {
            name: 'testworkspace:testlayer',
            title: 'Layer',
            visibility: true,
            storeIndex: 9,
            type: 'shapefile',
            url: 'base/web/client/test-resources/geoserver/wms',
            capabilities: {
                error: "unable to retrieve capabiltiies"
            }
        };
        const settings = {
            options: {opacity: 1}
        };
        const comp = ReactDOM.render(<WMSStyle element={l} settings={settings} />, document.getElementById("container"));
        expect(comp).toExist();
        const form = ReactTestUtils.scryRenderedDOMComponentsWithTag( comp, "form" );
        expect(form).toExist();

    });

});
