/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var ReactDOM = require('react-dom');
var Group = require('../DefaultGroup');

var expect = require('expect');

describe('test Group module component', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('test Group creation', () => {
        const layers = [{
            name: 'layer01',
            title: 'Layer 1',
            visibility: true,
            storeIndex: 0,
            type: 'wms',
            group: 'grp'
        }, {
            name: 'layer02',
            title: 'Layer 2',
            visibility: true,
            storeIndex: 1,
            type: 'wms',
            group: ''
        }];

        const group = {
            name: 'grp',
            title: 'Group',
            nodes: layers
        };
        const comp = ReactDOM.render(<Group node={group}><div/></Group>, document.getElementById("container"));
        expect(comp).toExist();

        const domNode = ReactDOM.findDOMNode(comp);
        expect(domNode).toExist();
        const children = domNode.children;
        expect(children.length).toBe(2);

        const container = children.item(0);
        expect(container.children.length).toBe(1);
    });

    it('test Group creation with filter', () => {
        const layers = [{
            name: 'layer01',
            title: 'Layer 1',
            visibility: true,
            storeIndex: 0,
            type: 'wms',
            group: 'grp'
        }, {
            name: 'layer02',
            title: 'Layer 2',
            visibility: true,
            storeIndex: 1,
            type: 'wms',
            group: ''
        }];

        const group = {
            name: 'grp',
            title: 'Group',
            nodes: layers
        };
        const comp = ReactDOM.render(<Group node={group} filter={(layer, node) => layer.group === node.name}><div/></Group>, document.getElementById("container"));
        expect(comp).toExist();

        const domNode = ReactDOM.findDOMNode(comp);
        expect(domNode).toExist();

        const children = domNode.children;
        expect(children.length).toBe(2);

        const container = children.item(1);
        expect(container.children.length).toBe(1);
    });

    it('test Group collapsed', () => {
        const layers = [{
            name: 'layer01',
            title: 'Layer 1',
            visibility: true,
            storeIndex: 0,
            type: 'wms',
            group: 'grp'
        }, {
            name: 'layer02',
            title: 'Layer 2',
            visibility: true,
            storeIndex: 1,
            type: 'wms',
            group: ''
        }];

        const group = {
            name: 'grp',
            title: 'Group',
            nodes: layers,
            expanded: false
        };
        const comp = ReactDOM.render(<Group node={group} filter={(layer, node) => layer.group === node.name}><div className="layer"/></Group>, document.getElementById("container"));
        expect(comp).toExist();

        const domNode = ReactDOM.findDOMNode(comp);
        expect(domNode).toExist();

        const children = domNode.getElementsByClassName('layer');
        expect(children.length).toBe(0);
    });

    it('test Group expanded', () => {
        const layers = [{
            name: 'layer01',
            title: 'Layer 1',
            visibility: true,
            storeIndex: 0,
            type: 'wms',
            group: 'grp'
        }, {
            name: 'layer02',
            title: 'Layer 2',
            visibility: true,
            storeIndex: 1,
            type: 'wms',
            group: ''
        }];

        const group = {
            name: 'grp',
            title: 'Group',
            nodes: layers
        };
        const comp = ReactDOM.render(<Group node={group} expanded filter={(layer, node) => layer.group === node.name}><div className="layer"/></Group>, document.getElementById("container"));
        expect(comp).toExist();

        const domNode = ReactDOM.findDOMNode(comp);
        expect(domNode).toExist();

        const children = domNode.getElementsByClassName('layer');
        expect(children.length).toBe(1);
    });

    it('test group visibility checkbox', () => {
        const layers = [{
            name: 'layer01',
            title: 'Layer 1',
            visibility: true,
            storeIndex: 0,
            type: 'wms',
            group: 'grp'
        }];
        const group = {
            name: 'grp',
            title: 'Group',
            nodes: layers
        };
        const actions = {
            propertiesChangeHandler: () => {}
        };
        let spy = expect.spyOn(actions, "propertiesChangeHandler");
        const comp = ReactDOM.render(<Group node={group} groupVisibilityCheckbox={true} visibilityCheckType="checkbox"
            propertiesChangeHandler={actions.propertiesChangeHandler}><div/></Group>,
            document.getElementById("container"));
        expect(comp).toExist();
        const cmpDom = ReactDOM.findDOMNode(comp);
        expect(cmpDom).toExist();
        const checkBox = cmpDom.getElementsByTagName('input')[0];
        expect(checkBox).toExist();
        checkBox.click();
        expect(spy.calls.length).toBe(1);
    });
    it('test group visibility glyph', () => {
        const layers = [{
            name: 'layer01',
            title: 'Layer 1',
            visibility: true,
            storeIndex: 0,
            type: 'wms',
            group: 'grp'
        }];
        const group = {
            name: 'grp',
            title: 'Group',
            nodes: layers
        };
        const actions = {
            propertiesChangeHandler: () => {}
        };
        let spy = expect.spyOn(actions, "propertiesChangeHandler");
        const comp = ReactDOM.render(<Group node={group} groupVisibilityCheckbox={true} visibilityCheckType="glyph"
            propertiesChangeHandler={actions.propertiesChangeHandler}><div/></Group>,
            document.getElementById("container"));
        expect(comp).toExist();
        const cmpDom = ReactDOM.findDOMNode(comp);
        expect(cmpDom).toExist();
        const checkBox = cmpDom.getElementsByClassName('glyphicon')[0];
        expect(checkBox).toExist();
        checkBox.click();
        expect(spy.calls.length).toBe(1);
    });

});
