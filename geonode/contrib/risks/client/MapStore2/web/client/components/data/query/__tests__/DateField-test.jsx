/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ReactDOM = require('react-dom');

const DateField = require('../DateField.jsx');

const expect = require('expect');

describe('DateField', () => {

    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates the DateField component with single date', () => {
        let operator = ">";
        let fieldName = "valueField";
        let fieldRowId = 200;
        let fieldValue = {startDate: new Date(86400000), endDate: null};

        const datefield = ReactDOM.render(
            <DateField attType="date"
                operator={operator}
                fieldName={fieldName}
                fieldRowId={fieldRowId}
                fieldValue={fieldValue}/>,
            document.getElementById("container")
        );

        expect(datefield).toExist();

        const dateFieldDOMNode = expect(ReactDOM.findDOMNode(datefield));
        expect(dateFieldDOMNode).toExist();

        let childNodes = dateFieldDOMNode.actual.getElementsByTagName('DIV');
        expect(childNodes.length).toBe(2);

        let dateRow = childNodes[0];
        expect(dateRow).toExist();

        expect(dateRow.childNodes.length).toBe(1);
    });

    it('creates the DateField component with date range', () => {
        let operator = "><";
        let fieldName = "valueField";
        let fieldRowId = 200;
        let fieldValue = {startDate: new Date(86400000), endDate: new Date(96400000)};

        const datefield = ReactDOM.render(
            <DateField attType="date"
                operator={operator}
                fieldName={fieldName}
                fieldRowId={fieldRowId}
                fieldValue={fieldValue}/>,
            document.getElementById("container")
        );

        expect(datefield).toExist();

        const dateFieldDOMNode = expect(ReactDOM.findDOMNode(datefield));
        expect(dateFieldDOMNode).toExist();

        let childNodes = dateFieldDOMNode.actual.getElementsByTagName('DIV');
        expect(childNodes.length).toBe(5);

        let dateRow = childNodes[0];
        expect(dateRow).toExist();

        expect(dateRow.childNodes.length).toBe(2);
    });
});
