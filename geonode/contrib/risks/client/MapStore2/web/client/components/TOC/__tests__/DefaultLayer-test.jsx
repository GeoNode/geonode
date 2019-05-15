/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var ReactDOM = require('react-dom');
var Layer = require('../DefaultLayer');
// var ConfirmButton = require('../../buttons/ConfirmButton');
var expect = require('expect');

const TestUtils = require('react-addons-test-utils');

describe('test DefaultLayer module component', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('tests DefaultLayer component creation (wms)', () => {
        const l = {
            name: 'layer00',
            title: 'Layer',
            visibility: true,
            storeIndex: 9,
            type: 'wms'
        };
        const comp = ReactDOM.render(<Layer visibilityCheckType="checkbox" node={l} />, document.getElementById("container"));
        expect(comp).toExist();

        const domNode = ReactDOM.findDOMNode(comp);
        expect(domNode).toExist();

        const checkbox = domNode.getElementsByTagName('input').item(0);
        expect(checkbox).toExist();
        expect(parseInt(checkbox.dataset.position, 10)).toBe(l.storeIndex);
        expect(checkbox.checked).toBe(l.visibility);

        const label = domNode.getElementsByTagName('span').item(0);
        expect(label).toExist();
        expect(label.innerHTML).toBe(l.title || l.name);
    });

    it('tests DefaultLayer component creation (no wms)', () => {
        const l = {
            name: 'layer00',
            title: 'Layer',
            visibility: false,
            storeIndex: 9
        };
        const comp = ReactDOM.render(<Layer visibilityCheckType="checkbox" node={l} />, document.getElementById("container"));
        expect(comp).toExist();

        const domNode = ReactDOM.findDOMNode(comp);
        expect(domNode).toExist();

        const checkbox = domNode.getElementsByTagName('input').item(0);
        expect(checkbox).toExist();
        expect(parseInt(checkbox.dataset.position, 10)).toBe(l.storeIndex);
        expect(checkbox.checked).toBe(l.visibility);

        const label = domNode.getElementsByTagName('span').item(0);
        expect(label).toExist();
        expect(label.innerHTML).toBe(l.title || l.name);
    });

    it('test change event', () => {
        let newProperties;
        let layer;

        let handler = (l, p) => {
            layer = l;
            newProperties = p;
        };

        const l = {
            name: 'layer00',
            id: 'layer00',
            title: 'Layer',
            visibility: false,
            storeIndex: 9
        };
        const comp = ReactDOM.render(
            <Layer
                visibilityCheckType="checkbox"
                propertiesChangeHandler={handler}
                node={l}
            />, document.getElementById("container"));
        expect(comp).toExist();

        const domNode = ReactDOM.findDOMNode(comp);
        expect(domNode).toExist();

        const checkbox = domNode.getElementsByTagName('input').item(0);
        expect(checkbox).toExist();

        checkbox.checked = !l.visibility;
        TestUtils.Simulate.change(checkbox, {
            target: {
                checked: !l.visibility
            }
        });
        expect(newProperties.visibility).toBe(!l.visibility);
        expect(layer).toBe('layer00');
    });

    it('tests legend tool', () => {
        const l = {
            name: 'layer00',
            title: 'Layer',
            visibility: true,
            storeIndex: 9,
            type: 'wms'
        };
        const actions = {
            onToggle: () => {}
        };
        let spy = expect.spyOn(actions, "onToggle");
        const comp = ReactDOM.render(<Layer visibilityCheckType="checkbox" node={l} activateLegendTool={true} onToggle={actions.onToggle}/>,
            document.getElementById("container"));
        expect(comp).toExist();
        const domNode = ReactDOM.findDOMNode(comp);
        expect(domNode).toExist();
        const tool = ReactDOM.findDOMNode(TestUtils.scryRenderedDOMComponentsWithClass(comp, "toc-legendTool")[0]);
        expect(tool).toExist();
        tool.click();
        expect(spy.calls.length).toBe(1);
    });

    it('tests zoom tool', () => {
        const l = {
            name: 'layer00',
            title: 'Layer',
            visibility: true,
            storeIndex: 9,
            type: 'wms',
            bbox: {
                crs: "EPSG:4326",
                bounds: {
                    minx: 11.0,
                    maxx: 13.0,
                    miny: 43.0,
                    maxy: 44.0
                }
            }
        };
        const actions = {
            onZoom: () => {}
        };
        let spy = expect.spyOn(actions, "onZoom");
        const comp = ReactDOM.render(<Layer visibilityCheckType="checkbox" node={l} activateZoomTool={true} onZoom={actions.onZoom}/>,
            document.getElementById("container"));
        expect(comp).toExist();
        const domNode = ReactDOM.findDOMNode(comp);
        expect(domNode).toExist();
        const tool = ReactDOM.findDOMNode(TestUtils.scryRenderedDOMComponentsWithClass(comp, "toc-zoomTool")[0]);
        expect(tool).toExist();
        tool.click();
        expect(spy.calls.length).toBe(1);
    });

    it('hide zoom tool when error occours', () => {
        const l = {
            name: 'layer00',
            title: 'Layer',
            visibility: true,
            storeIndex: 9,
            type: 'wms',
            loadingError: true,
            bbox: {
                crs: "EPSG:4326",
                bounds: {
                    minx: 11.0,
                    maxx: 13.0,
                    miny: 43.0,
                    maxy: 44.0
                }
            }
        };
        const actions = {
            onZoom: () => {}
        };
        const comp = ReactDOM.render(<Layer visibilityCheckType="checkbox" node={l} activateZoomTool={true} onZoom={actions.onZoom}/>,
            document.getElementById("container"));
        expect(comp).toExist();
        const domNode = ReactDOM.findDOMNode(comp);
        expect(domNode).toExist();
        const tool = ReactDOM.findDOMNode(TestUtils.scryRenderedDOMComponentsWithClass(comp, "toc-zoomTool")[0]);
        expect(tool).toNotExist();
    });

    it('tests removelayer tool', () => {
        const l = {
            name: 'layer000',
            title: 'Layer001',
            visibility: true,
            storeIndex: 9,
            type: 'wms'
        };
        const actions = {
            removeNode: () => {}
        };
        let spy = expect.spyOn(actions, "removeNode");
        const comp = ReactDOM.render(<Layer node={l} activateRemoveLayer={true} removeNode={actions.removeNode} />,
            document.getElementById("container"));
        expect(comp).toExist();
        const domNode = ReactDOM.findDOMNode(comp);
        expect(domNode).toExist();
        const tool = ReactDOM.findDOMNode(TestUtils.scryRenderedDOMComponentsWithClass(comp, "clayer_removal_button")[0]);
        expect(tool).toExist();
        tool.click();
        const confirmButton = document.getElementsByClassName("clayer_removal_confirm_button")[0];
        expect(confirmButton).toExist();
        confirmButton.click();
        expect(spy.calls.length).toBe(1);
    });

    it('tests settings tool', () => {
        const l = {
            id: 'layerId1',
            name: 'layer00',
            title: 'Layer',
            visibility: true,
            storeIndex: 9,
            type: 'wms',
            opacity: 0.5
        };
        const actions = {
            onSettings: () => {}
        };
        let spy = expect.spyOn(actions, "onSettings");
        const comp = ReactDOM.render(<Layer visibilityCheckType="checkbox" modalOptions={{animation: false}} node={l} activateSettingsTool={true} onSettings={actions.onSettings}/>,
            document.getElementById("container"));
        expect(comp).toExist();
        const domNode = ReactDOM.findDOMNode(comp);
        expect(domNode).toExist();
        const tool = ReactDOM.findDOMNode(TestUtils.scryRenderedDOMComponentsWithClass(comp, "glyphicon")[1]);
        expect(tool).toExist();
        tool.click();
        expect(spy.calls.length).toBe(1);
        expect(spy.calls[0].arguments.length).toBe(3);
        expect(spy.calls[0].arguments[0]).toBe("layerId1");
        expect(spy.calls[0].arguments[1]).toBe("layers");
        expect(spy.calls[0].arguments[2]).toEqual({opacity: 0.5});
    });

    it('test that settings modal is present only if all the requirements are met', () => {
        // helper function to render layers components
        var TestRoot = React.createClass({
            propTypes: {
                elements: React.PropTypes.array
            },
            render: function() {
                var elements = this.props.elements.map( function(element) {
                    return (<Layer key={element.layer.id}
                                visibilityCheckType="checkbox"
                               modalOptions={{animation: false}}
                               node={element.layer}
                               activateSettingsTool={true}
                               settings={element.settings}/>);
                });
                return <div>{elements}</div>;
            }
        });
        const render = function(elements) {
            ReactDOM.render(
                <TestRoot elements={elements} />,
                document.getElementById("container")
            );
        };
        // helper function to get current modals
        const getModals = function() {
            return document.getElementsByTagName("body")[0].getElementsByClassName('modal-dialog');
        };
        // no modals should be available
        const element1 = {layer: {id: 'layer1', name: 'layer1'}, settings: {}};
        const element2 = {layer: {id: 'layer2', name: 'layer2'}, settings: {}};
        render([element1, element2]);
        expect(getModals().length).toBe(0);
        // only one modal should be available (for layer3)
        let settings1 = {
            node: 'layer3',
            expanded: true,
            options: {
                opacity: 0.5
            }
        };
        const element3 = {layer: {id: 'layer3', name: 'layer3'}, settings: settings1};
        const element4 = {layer: {id: 'layer4', name: 'layer4'}, settings: settings1};
        render([element3, element4]);
        expect(getModals().length).toBe(1);
    });

    it('tests settings tool with a zero opacity', () => {
        // layer with a zero opacity value
        const layer = {
            id: 'layer1',
            name: 'layer1',
            opacity: 0.0
        };
        // on settings method to be invoked by the tool click with a spy on it
        const actions = {
            onSettings: () => {}
        };
        const spy = expect.spyOn(actions, "onSettings");
        // instanciating a layer component with the zero opacity layer
        const component = ReactDOM.render(
                <Layer modalOptions={{animation: false}}
                        visibilityCheckType="checkbox"
                       node={layer}
                       activateSettingsTool={true}
                       onSettings={actions.onSettings}/>,
                   document.getElementById("container"));
        expect(component).toExist();
        // let's find the settings tool and click on it
        const tool = ReactDOM.findDOMNode(
            TestUtils.scryRenderedDOMComponentsWithClass(component, "glyphicon")[1]);
        expect(tool).toExist();
        tool.click();
        // the onSettings method must have been invoked
        expect(spy.calls.length).toBe(1);
        expect(spy.calls[0].arguments.length).toBe(3);
        expect(spy.calls[0].arguments[0]).toBe("layer1");
        expect(spy.calls[0].arguments[1]).toBe("layers");
        expect(spy.calls[0].arguments[2]).toEqual({opacity: 0.0});
    });
});
