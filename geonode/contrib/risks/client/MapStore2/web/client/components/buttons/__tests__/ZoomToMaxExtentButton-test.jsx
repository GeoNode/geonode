/**
 * Copyright 2015-2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var ZoomToMaxExtentButton = require('../ZoomToMaxExtentButton');
var expect = require('expect');

// initializes Redux store
var Provider = require('react-redux').Provider;
var store = require('./../../../examples/myapp/stores/myappstore');

describe('This test for ZoomToMaxExtentButton', () => {
    beforeEach((done) => {
        document.body.innerHTML = '<div id="container"></div>';
        setTimeout(done);
    });

    afterEach((done) => {
        ReactDOM.unmountComponentAtNode(document.getElementById("container"));
        document.body.innerHTML = '';
        setTimeout(done);
    });

    // test DEFAULTS
    it('test default properties', () => {
        const zmeBtn = ReactDOM.render(
            <Provider store={store}>
                <ZoomToMaxExtentButton/>
            </Provider>,
            document.getElementById("container"));
        expect(zmeBtn).toExist();

        const zmeBtnNode = ReactDOM.findDOMNode(zmeBtn);
        expect(zmeBtnNode).toExist();
        expect(zmeBtnNode.id).toBe("mapstore-zoomtomaxextent");

        expect(zmeBtnNode).toExist();
        expect(zmeBtnNode.className.indexOf('default') >= 0).toBe(true);
        expect(zmeBtnNode.innerHTML).toExist();
    });

    it('test glyphicon property', () => {
        const zmeBtn = ReactDOM.render(
            <Provider store={store}>
                <ZoomToMaxExtentButton/>
            </Provider>,
            document.getElementById("container"));
        expect(zmeBtn).toExist();

        const zmeBtnNode = ReactDOM.findDOMNode(zmeBtn);
        expect(zmeBtnNode).toExist();
        expect(zmeBtnNode).toExist();
        const icons = zmeBtnNode.getElementsByTagName('span');
        expect(icons.length).toBe(1);
    });

    it('test glyphicon property with text', () => {
        const zmeBtn = ReactDOM.render(
            <Provider store={store}>
                <ZoomToMaxExtentButton glyphicon="info-sign" text="button"/>
            </Provider>,
            document.getElementById("container"));
        expect(zmeBtn).toExist();

        const zmeBtnNode = ReactDOM.findDOMNode(zmeBtn);
        expect(zmeBtnNode).toExist();
        expect(zmeBtnNode).toExist();

        const btnItems = zmeBtnNode.getElementsByTagName('span');
        expect(btnItems.length).toBe(1);

        expect(zmeBtnNode.innerText.indexOf("button") !== -1).toBe(true);
    });

    it('test if click on button launches the proper action', () => {

        let genericTest = function(btnType) {
            let actions = {
                changeMapView: (c, z, mb, ms) => {
                    return {c, z, mb, ms};
                }
            };
            let spy = expect.spyOn(actions, "changeMapView");
            var cmp = ReactDOM.render(
                <ZoomToMaxExtentButton
                    {...actions} btnType={btnType}
                    mapConfig={{
                        maxExtent: [-110, -110, 90, 90],
                        zoom: 10,
                        bbox: {
                            crs: 'EPSG:4326',
                            bounds: {
                                minx: "-15",
                                miny: "-15",
                                maxx: "5",
                                maxy: "5"
                            }
                        },
                        size: {
                            height: 100,
                            width: 100
                        }
                    }}
                />
            , document.getElementById("container"));
            expect(cmp).toExist();

            let componentSpy = expect.spyOn(cmp, 'zoomToMaxExtent').andCallThrough();

            const cmpDom = document.getElementById("mapstore-zoomtomaxextent");
            expect(cmpDom).toExist();

            cmpDom.click();

            // check that the correct zoom to extent method has been invoked
            expect(componentSpy.calls.length).toBe(1);
            componentSpy.restore();

            expect(spy.calls.length).toBe(1);
            expect(spy.calls[0].arguments.length).toBe(6);
        };

        genericTest("normal");
        genericTest("image");
    });

    it('create glyphicon with custom css class', () => {
        const zmeBtn = ReactDOM.render(
            <Provider store={store}>
                <ZoomToMaxExtentButton className="custom" glyphicon="info-sign" text="button"/>
            </Provider>,
            document.getElementById("container"));
        expect(zmeBtn).toExist();

        const zmeBtnNode = ReactDOM.findDOMNode(zmeBtn);
        expect(zmeBtnNode).toExist();

        expect(zmeBtnNode.className.indexOf('custom') !== -1).toBe(true);
    });

    it('test zoom to initial extent', () => {

        let genericTest = function(btnType) {
            let actions = {
                changeMapView: (c, z, mb, ms) => {
                    return {c, z, mb, ms};
                }
            };
            let actionsSpy = expect.spyOn(actions, "changeMapView");
            var cmp = ReactDOM.render(
                <ZoomToMaxExtentButton
                    {...actions} btnType={btnType}
                    useInitialExtent={true}
                    mapConfig={{
                        size: {
                            height: 100,
                            width: 100
                        }
                    }}
                    mapInitialConfig={{
                        zoom: 10,
                        center: {
                            x: 1250000.000000,
                            y: 5370000.000000,
                            crs: "EPSG:900913"
                        },
                        projection: "EPSG:900913"
                    }}
                />
            , document.getElementById("container"));
            expect(cmp).toExist();

            let componentSpy = expect.spyOn(cmp, 'zoomToInitialExtent').andCallThrough();

            const cmpDom = document.getElementById("mapstore-zoomtomaxextent");
            expect(cmpDom).toExist();

            cmpDom.click();

            // check that the correct zoom to extent method has been invoked
            expect(componentSpy.calls.length).toBe(1);
            componentSpy.restore();

            expect(actionsSpy.calls.length).toBe(1);
            expect(actionsSpy.calls[0].arguments.length).toBe(6);
            expect(actionsSpy.calls[0].arguments[0]).toExist();
            expect(actionsSpy.calls[0].arguments[1]).toExist();
            // the bbox is null since no hook was registered
            expect(actionsSpy.calls[0].arguments[2]).toNotExist();
            expect(actionsSpy.calls[0].arguments[3]).toExist();
            expect(actionsSpy.calls[0].arguments[4]).toNotExist();
            expect(actionsSpy.calls[0].arguments[5]).toExist();
        };

        genericTest("normal");
        genericTest("image");
    });
});
