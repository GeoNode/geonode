/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');

var React = require('react');
var ReactDOM = require('react-dom');
var BackgroundSwitcher = require('../BackgroundSwitcher');
var {Thumbnail} = require('react-bootstrap');

const TestUtils = require('react-addons-test-utils');

describe("test the BakckgroundSwitcher", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('test component creation', () => {
        let layers = [{
            "type": "osm",
            "title": "Open Street Map",
            "name": "mapnik",
            "group": "background",
            "visibility": true
        }, {
            "type": "wms",
            "url": "http://213.215.135.196/reflector/open/service",
            "visibility": false,
            "title": "e-Geos Ortofoto RealVista 1.0",
            "name": "rv1",
            "group": "background",
            "format": "image/png"
        }];
        const tb = ReactDOM.render(<BackgroundSwitcher layers={layers}/>, document.getElementById("container"));
        expect(tb).toExist();

    });

    it('create component without layers', () => {

        const tb = ReactDOM.render(<BackgroundSwitcher />, document.getElementById("container"));
        expect(tb).toExist();

    });

    it('test select handler', () => {
        const testHandlers = {
            propertiesChangeHandler: (pressed) => {return pressed; }
        };
        let layers = [{
            "type": "osm",
            "title": "Open Street Map",
            "name": "mapnik",
            "group": "background",
            "visibility": true
        }, {
            "type": "wms",
            "url": "http://213.215.135.196/reflector/open/service",
            "visibility": false,
            "title": "e-Geos Ortofoto RealVista 1.0",
            "name": "rv1",
            "group": "background",
            "format": "image/png"
        }];
        const spy = expect.spyOn(testHandlers, 'propertiesChangeHandler');
        var tb = ReactDOM.render(<BackgroundSwitcher layers={layers} propertiesChangeHandler={testHandlers.propertiesChangeHandler}/>, document.getElementById("container"));
        let thumbs = TestUtils.scryRenderedComponentsWithType(tb, Thumbnail);
        expect(thumbs.length).toBe(2);
        ReactDOM.findDOMNode(thumbs[0]).click();
        expect(spy.calls.length).toEqual(1);
    });
});
