/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const expect = require('expect');
const React = require('react');
const ReactDOM = require('react-dom');

const SimpleFilterField = require('../SimpleFilterField');

describe('SimpleFilterField', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('create a SimpleFilterField component without any props', () => {
        const cmp = ReactDOM.render(<SimpleFilterField/>, document.getElementById("container"));
        expect(cmp).toExist();
    });
    it('create a SimpleFilterField rendering radio', () => {
        let conf = {
                    "fieldId": 1,
                    "label": "Highway System",
                    "attribute": "highway_system",
                    "multivalue": false,
                    "values": ["state"],
                    "optionsValues": ["local", "state"],
                    "optionsLabels": {
                        "local": "Local",
                        "state": "State"
                    },
                    "required": true,
                    "sort": "ASC",
                    "defaultExpanded": true,
                    "collapsible": true
                    };
        const cmp = ReactDOM.render(<SimpleFilterField {...conf} />, document.getElementById("container"));
        expect(cmp).toExist();
        let node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        let inputs = node.getElementsByTagName("input");
        expect(inputs).toExist();
        expect(inputs.length).toBe(2);
        expect(inputs[0].getAttribute("type")).toBe("radio");
        inputs[0].checked = true;
        expect(inputs[0].checked).toBe(true);
        let e = {target: {value: "local"}};
        cmp.onRChange(e);
    });
    it('create a SimpleFilterField rendering checkbox', () => {
        let conf = {
                    "fieldId": 4,
                    "label": "Day(s) of Week",
                    "attribute": "day_of_week",
                    "checkboxStyle": {"width": 80},
                    "multivalue": true,
                    "required": true,
                    "sort": "ASC",
                    "toolbar": true,
                    "type": "list",
                    "operator": "=",
                    "defaultExpanded": true,
                    "collapsible": true,
                    "optionsValues": ["Monday", "Tuesday", "Wednesday"],
                    "values": ["Monday", "Tuesday", "Wednesday"],
                    "defaultOptions": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                };
        const cmp = ReactDOM.render(<SimpleFilterField {...conf} />, document.getElementById("container"));
        expect(cmp).toExist();
        let node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        let inputs = node.getElementsByTagName("input");
        expect(inputs).toExist();
        expect(inputs.length).toBe(3);
        expect(inputs[0].getAttribute("type")).toBe("checkbox");
        expect(inputs[0].checked).toBe(true);
        expect(inputs[1].checked).toBe(true);
        expect(inputs[2].checked).toBe(true);
        inputs[0].checked = true;
        let e = {target: {value: "Monday", checked: false}};
        cmp.onCheckChange(e);
        e = {target: {value: "Monday", checked: true}};
        cmp.onCheckChange(e);

    });
    it('create a SimpleFilterField rendering combo single with bool', () => {
        let conf = {
                    "fieldId": 4,
                    "label": "Day(s) of Week",
                    "attribute": "day_of_week",
                    "multivalue": false,
                    "sort": "ASC",
                    "toolbar": true,
                    "type": "list",
                    "operator": "=",
                    "defaultExpanded": true,
                    "collapsible": true,
                    "optionsValues": [false, true, null],
                    "values": [false],
                    "combo": true,
                     "optionsLabels": {
                        "true": "Y",
                        "false": "N",
                        "null": "Empty"
                    }
                };
        const cmp = ReactDOM.render(<SimpleFilterField {...conf} />, document.getElementById("container"));
        expect(cmp).toExist();
        cmp.onComboChange("", "", "null");
    });
    it('create a SimpleFilterField rendering combo multi', () => {
        let conf = {
                    "fieldId": 4,
                    "label": "Day(s) of Week",
                    "attribute": "day_of_week",
                    "checkboxStyle": {"width": 80},
                    "multivalue": true,
                    "required": true,
                    "sort": "DESC",
                    "toolbar": true,
                    "combo": true,
                    "type": "list",
                    "operator": "=",
                    "defaultExpanded": true,
                    "collapsible": true,
                    "optionsValues": ["Monday", "Tuesday", "Wednesday"],
                    "values": ["Monday", "Tuesday", "Wednesday"]
                };
        const cmp = ReactDOM.render(<SimpleFilterField {...conf} />, document.getElementById("container"));
        expect(cmp).toExist();
        cmp.selectAll();
        cmp.clearAll();
        cmp.shouldComponentUpdate("");
    });
    it('create a SimpleFilterField rendering number', () => {
        let conf = {
                    "fieldId": 4,
                    "label": "Day(s) of Week",
                    "attribute": "day_of_week",
                    "sort": "DESC",
                    "type": "number",
                    "operator": "><",
                    "defaultExpanded": true,
                    "collapsible": true
                };
        const cmp = ReactDOM.render(<SimpleFilterField {...conf} />, document.getElementById("container"));
        expect(cmp).toExist();
        cmp.selectAll();
        cmp.clearAll();
        cmp.onNumberChange(4, "day_of_week", 10);
        cmp.onNumberException(4, "exception");
    });
    it('create a SimpleFilterField rendering text', () => {
        let conf = {
                    "fieldId": 4,
                    "label": "Day(s) of Week",
                    "attribute": "day_of_week",
                    "sort": "DESC",
                    "type": "text",
                    "operator": "ilike",
                    "defaultExpanded": true,
                    "collapsible": true
                };
        const cmp = ReactDOM.render(<SimpleFilterField {...conf} />, document.getElementById("container"));
        expect(cmp).toExist();
        cmp.selectAll();
        cmp.clearAll();
        cmp.onTextChange(4, "day_of_week", "10");
    });
});
