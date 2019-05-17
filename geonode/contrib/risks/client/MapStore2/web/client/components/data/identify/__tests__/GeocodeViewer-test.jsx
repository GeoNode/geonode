/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ReactDOM = require('react-dom');

const GeocodeViewer = require('../GeocodeViewer.jsx');

const expect = require('expect');

const TestUtils = require('react-addons-test-utils');

class Wrapper extends React.Component {
    render() {
        return this.props.children;
    }
}

describe('GeocodeViewer', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates the GeocodeViewer component with defaults', () => {
        let component = <Wrapper><GeocodeViewer modalOptions={{animation: false}} show="true" latlng={{lat: 42, lng: 10}} showModalReverse="false"/></Wrapper>;
        const header = ReactDOM.render(
            component,
            document.getElementById("container")
        );

        expect(header).toExist();
    });

    it('creates the GeocodeViewer component with latlng', () => {
        let component = <Wrapper><GeocodeViewer modalOptions={{animation: false}} show="true" latlng={{lat: 42, lng: 10}} showModalReverse="false"/></Wrapper>;
        const header = ReactDOM.render(
            component,
            document.getElementById("container")
        );

        expect(header).toExist();
        const dom = ReactDOM.findDOMNode(header);
        expect(dom.innerHTML.indexOf('42') !== -1).toBe(true);
        expect(dom.innerHTML.indexOf('10') !== -1).toBe(true);
    });

    it('test click handler and modal', () => {
        const testHandlers = {
            clickHandler: (pressed) => {return pressed; }
        };
        const spy = expect.spyOn(testHandlers, 'clickHandler');
        var geocode = ReactDOM.render(<Wrapper><GeocodeViewer modalOptions={{animation: false}} latlng={{lat: 42, lng: 10}} showRevGeocode={testHandlers.clickHandler} showModalReverse={true}/></Wrapper>, document.getElementById("container"));
        let elem = TestUtils.findRenderedDOMComponentWithTag(geocode, "button");

        const getModals = function() {
            return document.getElementsByTagName("body")[0].getElementsByClassName('modal-dialog');
        };

        expect(getModals().length).toBe(1);

        expect(elem).toExist();
        ReactDOM.findDOMNode(elem).click();
        expect(spy.calls.length).toEqual(1);
        expect(spy.calls[0].arguments[0].lat).toEqual(42);
        expect(spy.calls[0].arguments[0].lng).toEqual(10);
    });
});
