/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var ReactDOM = require('react-dom');
var ol = require('openlayers');
var ScaleBar = require('../ScaleBar');
var expect = require('expect');

describe('Openlayers ScaleBar component', () => {
    let map;
    beforeEach((done) => {
        document.body.innerHTML = '<div id="map"></div><div id="container"></div>';
        map = new ol.Map({
          layers: [
          ],
          controls: ol.control.defaults({
            attributionOptions: /** @type {olx.control.AttributionOptions} */ ({
              collapsible: false
            })
          }),
          target: 'map',
          view: new ol.View({
            center: [0, 0],
            zoom: 5
          })
        });
        setTimeout(done);
    });

    afterEach((done) => {
        map.setTarget(null);
        document.body.innerHTML = '';
        setTimeout(done);
    });

    it('create ScaleBar with defaults', () => {
        const sb = ReactDOM.render(<ScaleBar map={map}/>, document.getElementById("container"));
        expect(sb).toExist();
        const domMap = map.getViewport();
        const scaleBars = domMap.getElementsByClassName('ol-scale-line');
        expect(scaleBars.length).toBe(1);
    });
});
