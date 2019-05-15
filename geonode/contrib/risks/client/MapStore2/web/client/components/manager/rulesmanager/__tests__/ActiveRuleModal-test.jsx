/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const ReactDOM = require('react-dom');
const ActiveRuleModal = require('../ActiveRuleModal.jsx');
const expect = require('expect');
const Wrapper = React.createClass({
    render() {
        return this.props.children;
    }
});
describe('test rule edit modal component', () => {

    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('creates the component with defaults', () => {
        const ruleAttributes = ReactDOM.render(<ActiveRuleModal/>, document.getElementById("container"));
        expect(ruleAttributes).toExist(null);


    });
    it('shows the component', () => {
        const ruleAttributes = ReactDOM.render(<Wrapper><ActiveRuleModal animation={false} activeRule={{status: "new"}} /></Wrapper>, document.getElementById("container"));
        expect(ruleAttributes).toExist();
        const getModals = function() {
            return document.getElementsByTagName("body")[0].getElementsByClassName('modal-dialog');
        };
        expect(getModals().length).toBe(1);
    });
});
