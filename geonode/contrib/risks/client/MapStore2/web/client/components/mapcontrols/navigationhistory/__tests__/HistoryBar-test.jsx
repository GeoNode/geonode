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
var HistoryBar = require('../HistoryBar');

describe('HistoryBar', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('checks default', () => {

        const cmp = ReactDOM.render(<HistoryBar/>, document.getElementById("container"));
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();

        const normalButtons = cmpDom.getElementsByTagName("button");
        expect(normalButtons.length === 2);

        const imageButtons = cmpDom.getElementsByTagName("img");
        expect(imageButtons.length === 0);
    });

    it('checks undo and redo button click', () => {

        let genericTest = function(btnType) {
            const handlers = {
                onclick() {}
            };
            let spy = expect.spyOn(handlers, "onclick");
            const cmp = ReactDOM.render(<HistoryBar btnType={btnType} undoBtnProps={{ onClick: handlers.onclick}}
                redoBtnProps={{ onClick: handlers.onclick}}/>, document.getElementById("container"));
            const cmpDom = ReactDOM.findDOMNode(cmp);
            const undo = btnType === "normal" ? cmpDom.getElementsByTagName("button").item(0)
                                              : cmpDom.getElementsByTagName("img").item(0);
            const redo = btnType === "normal" ? cmpDom.getElementsByTagName("button").item(1)
                                              : cmpDom.getElementsByTagName("img").item(1);
            undo.click();
            redo.click();
            expect(spy.calls.length).toBe(2);
        };

        genericTest("normal");
        genericTest("image");
    });

    it('checks with image buttons', () => {

        const cmp = ReactDOM.render(<HistoryBar btnType="image"/>, document.getElementById("container"));
        expect(cmp).toExist();

        const cmpDom = ReactDOM.findDOMNode(cmp);
        expect(cmpDom).toExist();

        const normalButtons = cmpDom.getElementsByTagName("button");
        expect(normalButtons.length === 0);

        const imageButtons = cmpDom.getElementsByTagName("img");
        expect(imageButtons.length === 2);
    });
});
