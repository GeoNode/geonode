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
const SharePanel = require('../SharePanel');


describe("The SharePanel component", () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('is created with defaults', () => {
        const cmp = ReactDOM.render(<SharePanel getCount={()=>0} shareUrl="www.geo-solutions.it"/>, document.getElementById("container"));
        expect(cmp).toExist();
    });

    it('should be visible', () => {
        const cmpSharePanel = ReactDOM.render(<SharePanel getCount={()=>0} shareUrl="www.geo-solutions.it" isVisible={true} />, document.getElementById("container"));
        expect(cmpSharePanel).toExist();

        const cmpSharePanelDom = ReactDOM.findDOMNode(cmpSharePanel);
        expect(cmpSharePanelDom).toExist();
        expect(cmpSharePanelDom.id).toEqual("share-panel-dialog");

    });

    it('should not be visible', () => {
        const cmpSharePanel = ReactDOM.render(<SharePanel getCount={()=>0} shareUrl="www.geo-solutions.it" isVisible={false} />, document.getElementById("container"));
        expect(cmpSharePanel).toExist();
        const cmpSharePanelDom = ReactDOM.findDOMNode(cmpSharePanel);
        expect(cmpSharePanelDom).toBeFalsy();

    });

});
