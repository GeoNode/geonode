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
var HTMLViewer = require('../HTMLViewer');
var JSONViewer = require('../JSONViewer');
var TextViewer = require('../TextViewer');

const SimpleRowViewer = (props) => {
    return <div>{['name', 'description'].map((key) => <span>{key}:{props[key]}</span>)}</div>;
};

describe('Identity Viewers', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('test HTMLViewer', () => {
        const cmp = ReactDOM.render(<HTMLViewer response="<span class='testclass'>test</span>" />, document.getElementById("container"));
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();

        expect(cmpDom.getElementsByClassName("testclass").length).toBe(1);
    });

    it('test TextViewer', () => {
        const cmp = ReactDOM.render(<TextViewer response="testtext" />, document.getElementById("container"));
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();

        expect(cmpDom.innerHTML.indexOf('testtext') !== -1).toBe(true);
    });

    it('test JSONViewer', () => {
        const cmp = ReactDOM.render(<JSONViewer response={{
            features: [{
                id: 1,
                properties: {
                    name: 'myname',
                    description: 'mydescription'
                }
            }]
        }} rowViewer={SimpleRowViewer}/>, document.getElementById("container"));
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();

        expect(cmpDom.innerHTML.indexOf('myname') !== -1).toBe(true);
        expect(cmpDom.innerHTML.indexOf('mydescription') !== -1).toBe(true);
    });
});
