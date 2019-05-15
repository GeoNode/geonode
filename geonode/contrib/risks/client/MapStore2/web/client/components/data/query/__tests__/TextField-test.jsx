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

const TextField = require('../TextField');

describe('TextField', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('create a TextField component without any props', () => {
        const cmp = ReactDOM.render(<TextField/>, document.getElementById("container"));
        expect(cmp).toExist();
    });
    it('create a TextField with isNull operator', () => {
        let conf = {
                    fieldRowId: 846,
                    groupId: 1,
                    attribute: "FAMILIES",
                    operator: "isNull",
                    fieldValue: '',
                    type: "string"
                    };
        const cmp = ReactDOM.render(<TextField {...conf} />, document.getElementById("container"));
        expect(cmp).toExist();
        let node = ReactDOM.findDOMNode(cmp);
        expect(node).toExist();
        let inputs = node.getElementsByTagName("input");
        expect(inputs).toExist();
        expect(inputs.length).toBe(1);
        cmp.changeText({target: { value: "1"}});


    });
});
