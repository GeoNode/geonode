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
var ol = require('openlayers');
var Overview = require('../Overview');


describe('Openlayers Overview component', () => {
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

    it('create Overview with defaults', () => {
        const ov = ReactDOM.render(<Overview map={map}/>, document.getElementById("container"));
        expect(ov).toExist();
        const domMap = map.getViewport();
        const overview = domMap.getElementsByClassName('ol-overviewmap');
        expect(overview.length).toBe(1);
    });
});
