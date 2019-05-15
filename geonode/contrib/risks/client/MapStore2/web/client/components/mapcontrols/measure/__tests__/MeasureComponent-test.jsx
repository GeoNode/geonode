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
var MeasureComponent = require('../MeasureComponent');
var NumberFormat = require('../../../I18N/Number');

const assign = require('object-assign');

describe("test the MeasureComponent", () => {
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
        let measurement = {};
        const mc = ReactDOM.render(<MeasureComponent measurement={measurement}/>, document.getElementById("container"));
        expect(mc).toExist();
    });

    it('test creation of button UIs ', () => {
        let measurement = {};
        const mc = ReactDOM.render(<MeasureComponent measurement={measurement}/>, document.getElementById("container"));
        expect(mc).toExist();
        const domNode = ReactDOM.findDOMNode(mc);
        expect(domNode).toExist();
        const domButtons = domNode.getElementsByTagName('button');
        expect(domButtons).toExist();
        expect(domButtons.length).toBe(3);
    });

    it('test creation of measurement result panel UI ', () => {
        let measurement = {};
        const mc = ReactDOM.render(<MeasureComponent measurement={measurement}/>, document.getElementById("container"));
        expect(mc).toExist();
        const domNode = ReactDOM.findDOMNode(mc);
        expect(domNode).toExist();
        const domResultPanel = document.getElementById('measure-result-panel');
        expect(domResultPanel).toExist();
    });

    it('test line activation', () => {
        let newMeasureState;
        let measurement = {
            geomType: null
        };
        const cmp = ReactDOM.render(
            <MeasureComponent
                measurement={measurement}
                toggleMeasure={(data) => {
                    newMeasureState = data;
                }}
                lineMeasureEnabled={false} />, document.getElementById("container")
        );
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();

        const buttons = cmpDom.getElementsByTagName('button');
        expect(buttons.length).toBe(3);

        const lineBtn = buttons.item(0);
        lineBtn.click();

        expect(newMeasureState).toExist();
        expect(newMeasureState.geomType).toBe('LineString');
    });

    it('test area activation', () => {
        let newMeasureState;
        let measurement = {
            geomType: null
        };
        const cmp = ReactDOM.render(
            <MeasureComponent
                measurement={measurement}
                toggleMeasure={(data) => {
                    newMeasureState = data;
                }}
                areaMeasureEnabled={false} />, document.getElementById("container")
        );
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();

        const buttons = cmpDom.getElementsByTagName('button');
        expect(buttons.length).toBe(3);

        const areaBtn = buttons.item(1);
        areaBtn.click();

        expect(newMeasureState).toExist();
        expect(newMeasureState.geomType).toBe('Polygon');
    });

    it('test bearing activation', () => {
        let newMeasureState;
        let measurement = {
            geomType: null
        };
        const cmp = ReactDOM.render(
            <MeasureComponent
                measurement={measurement}
                toggleMeasure={(data) => {
                    newMeasureState = data;
                }}
                bearingMeasureEnabled={false} />, document.getElementById("container")
        );
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();

        const buttons = cmpDom.getElementsByTagName('button');
        expect(buttons.length).toBe(3);

        const bearingBtn = buttons.item(2);
        bearingBtn.click();

        expect(newMeasureState).toExist();
        expect(newMeasureState.geomType).toBe('Bearing');
    });

    it('test measurements resetting', () => {
        let newMeasureState;
        let measurement = {
            geomType: 'Bearing'
        };
        const cmp = ReactDOM.render(
            <MeasureComponent
                measurement={measurement}
                toggleMeasure={(data) => {
                    newMeasureState = data;
                }}
                withReset={true}
            />, document.getElementById("container")
        );
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();

        const buttons = cmpDom.getElementsByTagName('button');
        expect(buttons.length).toBe(4);

        const resetBtn = buttons.item(3);

        // Dectivate
        resetBtn.click();

        expect(newMeasureState).toExist();
        expect(newMeasureState.geomType).toBe(null);
    });

    it('test bearing format', () => {
        let measurement = {
            lineMeasureEnabled: false,
            areaMeasureEnabled: false,
            bearingMeasureEnabled: false,
            geomType: 'LineString',
            len: 0,
            area: 0,
            bearing: 0
        };
        let cmp = ReactDOM.render(
            <MeasureComponent measurement={measurement}/>, document.getElementById("container")
        );
        expect(cmp).toExist();

        const bearingSpan = document.getElementById('measure-bearing-res');
        expect(bearingSpan).toExist();

        cmp = ReactDOM.render(
            <MeasureComponent measurement={assign({}, measurement, {bearing: 45})}/>, document.getElementById("container")
        );
        expect(bearingSpan.innerHTML).toBe("N 45° 0' 0''  E");

        cmp = ReactDOM.render(
            <MeasureComponent measurement={assign({}, measurement, {bearing: 135})}/>, document.getElementById("container")
        );
        expect(bearingSpan.innerHTML).toBe("S 45° 0' 0''  E");

        cmp = ReactDOM.render(
            <MeasureComponent measurement={assign({}, measurement, {bearing: 225})}/>, document.getElementById("container")
        );
        expect(bearingSpan.innerHTML).toBe("S 45° 0' 0''  W");

        cmp = ReactDOM.render(
            <MeasureComponent measurement={assign({}, measurement, {bearing: 315})}/>, document.getElementById("container")
        );
        expect(bearingSpan.innerHTML).toBe("N 45° 0' 0''  W");
    });
    it('test uom format area and lenght', () => {
        let measurement = {
            lineMeasureEnabled: false,
            areaMeasureEnabled: false,
            bearingMeasureEnabled: false,
            geomType: 'LineString',
            len: 0,
            area: 0,
            bearing: 0
        };
        let decimalFormat = {style: "decimal", minimumIntegerDigits: 1, maximumFractionDigits: 2, minimumFractionDigits: 2};
        let cmp = ReactDOM.render(
            <MeasureComponent uom={{
                length: {unit: 'km', label: 'km'},
                area: {unit: 'sqkm', label: 'km²'}
            }} measurement={measurement}/>, document.getElementById("container")
        );
        expect(cmp).toExist();

        const lenSpan = document.getElementById('measure-len-res');
        expect(lenSpan).toExist();

        let testDiv = document.createElement("div");
        document.body.appendChild(testDiv);
        let val = ReactDOM.findDOMNode(ReactDOM.render((<span><NumberFormat key="len" numberParams={decimalFormat} value={10} />km</span>), testDiv));
        cmp = ReactDOM.render(
            <MeasureComponent uom={{
                length: {unit: 'km', label: 'km'},
                area: {unit: 'sqkm', label: 'km²'}
            }} measurement={assign({}, measurement, {len: 10000})}/>, document.getElementById("container")
        );
        expect(lenSpan.firstChild.innerHTML).toBe(val.firstChild.innerHTML);
        expect(lenSpan.lastChild.innerHTML).toBe(val.lastChild.innerHTML);

        const areaSpan = document.getElementById('measure-area-res');
        expect(areaSpan).toExist();
        val = ReactDOM.findDOMNode(ReactDOM.render((<span><NumberFormat key="len" numberParams={decimalFormat} value={1} />km²</span>), testDiv));
        cmp = ReactDOM.render(
            <MeasureComponent uom={{
                length: {unit: 'km', label: 'km'},
                area: {unit: 'sqkm', label: 'km²'}
            }} measurement={assign({}, measurement, {geomType: 'Polygon', area: 1000000})}/>, document.getElementById("container")
        );
        expect(areaSpan.firstChild.innerHTML).toBe(val.firstChild.innerHTML);
        expect(areaSpan.lastChild.innerHTML).toBe(val.lastChild.innerHTML);
    });
});
