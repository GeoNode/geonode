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
var FeatureInfoFormatSelector = require('../FeatureInfoFormatSelector');

const TestUtils = require('react-addons-test-utils');

describe('FeatureInfoFormatSelector', () => {
    const data = {
        k0: "v0",
        k1: "v1",
        k2: "v2"
    };
    const defaultVal = data.k1;

    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('test list filling', () => {
        const cmp = ReactDOM.render(
            <FeatureInfoFormatSelector
                availableInfoFormat={data}
                infoFormat={defaultVal}/>
            , document.getElementById("container"));
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();

        const select = cmpDom.getElementsByTagName("select").item(0);
        const opts = select.childNodes;
        expect(opts.length).toBe(3);
        expect(Array.prototype.reduce.call(opts, (prev, opt, index) => {
            let val = opt.value;
            let lbl = opt.innerHTML;

            return prev
                && val === data["k" + index]
                && lbl === "k" + index;
        }, true)).toBe(true);

        expect(Array.prototype.reduce.call(opts, (prev, opt) => {
            return prev
                && opt.value === defaultVal ? opt.selected : !opt.selected;
        }, true)).toBe(true);
    });

    it('test onChange handler', () => {
        let newFormat;
        const cmp = ReactDOM.render(
            <FeatureInfoFormatSelector
                availableInfoFormat={data}
                infoFormat={defaultVal}
                onInfoFormatChange={(format) => {
                    newFormat = format;
                }}/>
            , document.getElementById("container"));
        const cmpDom = ReactDOM.findDOMNode(cmp);
        const select = cmpDom.getElementsByTagName("select").item(0);

        select.value = "v2";
        TestUtils.Simulate.change(select, {target: {value: 'v2'}});

        expect(newFormat).toBe('v2');
    });

});
