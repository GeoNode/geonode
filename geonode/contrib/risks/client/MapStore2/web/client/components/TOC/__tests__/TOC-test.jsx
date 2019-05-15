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

var TOC = require('../TOC');
var Group = require('../DefaultGroup');
var Layer = require('../DefaultLayer');

let testData = [
    {
        name: "G0",
        title: "G0",
        nodes: [
            {
                group: 'G0',
                name: 'L1',
                visibility: false
            }, {
                group: 'G0',
                name: 'L2',
                visibility: true
            }
        ]
    },
    {
        name: "G1",
        title: "G1",
        nodes: [
            {
                group: 'G1',
                name: 'L3',
                visibility: true
            }, {
                group: 'G1',
                name: 'L4',
                visibility: false
            }
        ]
    },
    {
        name: "G2",
        title: "G2",
        nodes: [
            {
                group: 'G2',
                name: 'L5',
                visibility: true
            }, {
                group: 'G2',
                name: 'L6',
                visibility: false
            }, {
                group: 'G2',
                name: 'L7',
                visibility: true
            }
        ]
    }
];

let layers = [
    {
        group: 'G2',
        name: 'L5',
        visibility: true
    }, {
        group: 'G2',
        name: 'L6',
        visibility: false
    }, {
        group: 'G2',
        name: 'L7',
        visibility: true
    }
];

describe('Layers component', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHtml = '';
        setTimeout(done);
    });

    it('test Layers component that use group as own direct children', () => {

        const element = ReactDOM.render(
            <TOC nodes={testData}>
                <Group>
                    <Layer/>
                </Group>
            </TOC>,
        document.getElementById("container"));
        expect(element).toExist();

        const domNode = ReactDOM.findDOMNode(element);
        expect(domNode).toExist();
        expect(domNode.children.length).toBe(3);
    });

    it('test filter function', () => {
        var filter = (layer) => {
            return layer.name !== 'G2';
        };

        const element = ReactDOM.render(
            <TOC filter={filter} nodes={testData}>
                <Group>
                    <Layer/>
                </Group>
            </TOC>,
        document.getElementById("container"));
        expect(element).toExist();

        const domNode = ReactDOM.findDOMNode(element);
        expect(domNode).toExist();
        expect(domNode.children.length).toBe(2);
    });

    it('test Layers component that use layers as own direct children', () => {

        var element = ReactDOM.render(
            <TOC nodes={layers}>
                <Layer/>
            </TOC>,
        document.getElementById("container"));
        expect(element).toExist();

        const domNode = ReactDOM.findDOMNode(element);
        expect(domNode).toExist();
        expect(domNode.children.length).toBe(layers.length);
    });

    it('tests Layers component sortable', () => {
        const comp = ReactDOM.render(<TOC onSort={() => {}} nodes={layers}><Layer/></TOC>, document.getElementById("container"));

        const domNode = ReactDOM.findDOMNode(comp);

        const sortable = domNode.getElementsByClassName('Sortable');
        expect(sortable).toExist();
        expect(sortable.length).toBe(1);

        const sortableItem = domNode.getElementsByClassName('SortableItem');
        expect(sortableItem).toExist();
        expect(sortableItem.length).toBe(3);
    });
});
