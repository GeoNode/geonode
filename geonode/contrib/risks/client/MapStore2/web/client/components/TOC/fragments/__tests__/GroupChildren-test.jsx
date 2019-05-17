/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var ReactDOM = require('react-dom');
var GroupChildren = require('../GroupChildren');
var Node = require('../../Node');

var expect = require('expect');

describe('test GroupChildren module component', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('tests GroupChildren component creation', () => {
        const l1 = {
            name: 'layer00',
            title: 'Layer',
            visibility: true,
            storeIndex: 9,
            type: 'wms',
            url: 'fakeurl'
        };

        const g = {
            name: "g1",
            title: "G1",
            nodes: [l1]
        };
        const comp = ReactDOM.render(<GroupChildren node={g}><div className="layer"></div></GroupChildren>, document.getElementById("container"));

        const domNode = ReactDOM.findDOMNode(comp);
        expect(domNode).toExist();

        const layers = domNode.getElementsByClassName('layer');
        expect(layers).toExist();
        expect(layers.length).toBe(1);
    });

    it('tests GroupChildren component sortable', () => {
        const l1 = {
            name: 'layer00',
            title: 'Layer',
            visibility: true,
            storeIndex: 9,
            type: 'wms',
            url: 'fakeurl'
        };

        const g = {
            name: "g1",
            title: "G1",
            nodes: [l1]
        };
        const comp = ReactDOM.render(<GroupChildren onSort={() => {}} node={g}><Node node={l1}/></GroupChildren>, document.getElementById("container"));

        const domNode = ReactDOM.findDOMNode(comp);

        const sortable = domNode.getElementsByClassName('Sortable');
        expect(sortable).toExist();
        expect(sortable.length).toBe(1);

        const sortableItem = domNode.getElementsByClassName('SortableItem');
        expect(sortableItem).toExist();
        expect(sortableItem.length).toBe(1);
    });
});
