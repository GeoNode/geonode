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
var OpenlayersLayer = require('../Layer.jsx');
var expect = require('expect');
var assign = require('object-assign');
require('../../../../utils/openlayers/Layers');
require('../plugins/OSMLayer');
require('../plugins/WMSLayer');
require('../plugins/WMTSLayer');
require('../plugins/GoogleLayer');
require('../plugins/BingLayer');
require('../plugins/MapQuest');
require('../plugins/VectorLayer');
require('../plugins/GraticuleLayer');
require('../plugins/OverlayLayer');

describe('Openlayers layer', () => {
    document.body.innerHTML = '<div id="map"></div>';
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

    it('missing layer', () => {
        var source = {
            "P_TYPE": "wrong ptype key"
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer source={source}
                  map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(0);
    });

    it('creates a unknown source layer', () => {
        var options = {
            "name": "FAKE"
        };
        var source = {
            "ptype": "FAKE",
            "url": "http://sample.server/geoserver/wms"
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer source={source}
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        // count layers
        expect(map.getLayers().getLength()).toBe(0);
    });

    it('creates source with missing ptype', () => {
        var options = {
            "name": "FAKE"
        };
        var source = {
            "P_TYPE": "wrong ptype key"
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer source={source}
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(0);
    });
    it('creates a osm layer for openlayers map', () => {
        var options = {};
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="osm"
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
    });
    it('creates a osm layer for openlayers map', () => {
        var options = {
            "source": "osm",
            "title": "Open Street Map",
            "name": "mapnik",
            "group": "background"
        };
        // create layer
        var layer = ReactDOM.render(
            <OpenlayersLayer type="osm"
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
    });

    it('creates a wms layer for openlayers map', () => {
        var options = {
            "type": "wms",
            "visibility": true,
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png",
            "url": "http://sample.server/geoserver/wms"
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="wms"
                 options={options} map={map}/>, document.getElementById("container"));


        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
        expect(map.getLayers().item(0).getSource().urls.length).toBe(1);
    });

    it('creates a wmts layer for openlayers map', () => {
        var options = {
            "type": "wmts",
            "visibility": true,
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png",
            "tileMatrixSet": "EPSG:900913",
            "url": "http://sample.server/geoserver/gwc/service/wmts"
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="wmts"
                 options={options} map={map}/>, document.getElementById("container"));


        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
        expect(map.getLayers().item(0).getSource().urls.length).toBe(1);
    });

    it('creates a wmts layer with multiple urls for openlayers map', () => {
        var options = {
            "type": "wmts",
            "visibility": true,
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png",
            "tileMatrixSet": "EPSG:900913",
            "url": ["http://sample.server/geoserver/gwc/service/wmts", "http://sample.server/geoserver/gwc/service/wmts"]
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="wmts"
                 options={options} map={map}/>, document.getElementById("container"));


        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
        expect(map.getLayers().item(0).getSource().urls.length).toBe(2);
    });

    it('creates a wms layer for openlayers map with custom tileSize', () => {
        var options = {
            "type": "wms",
            "visibility": true,
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png",
            "tileSize": 512,
            "url": "http://sample.server/geoserver/wms"
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="wms"
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
        expect(map.getLayers().item(0).getProperties().source.getTileGrid().getTileSize()).toBe(512);
    });

    it('creates a wms layer with multiple urls for openlayers map', () => {
        var options = {
            "type": "wms",
            "visibility": true,
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png",
            "url": ["http://sample.server/geoserver/wms", "http://sample.server/geoserver/wms"]
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="wms"
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
        expect(map.getLayers().item(0).getSource().urls.length).toBe(2);
    });

    it('creates a wms layer with custom origin', () => {
        var options = {
            "type": "wms",
            "visibility": true,
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png",
            "origin": [0, 0],
            "url": ["http://sample.server/geoserver/wms"]
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="wms"
                 options={options} map={map}/>, document.getElementById("container"));


        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
        expect(map.getLayers().item(0).getSource().getTileGrid().getOrigin()).toEqual([0, 0]);
    });

    it('creates a wms layer with proxy  for openlayers map', () => {
        var options = {
            "type": "wms",
            "visibility": true,
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png",
            "forceProxy": true,
            "url": ["http://sample.server/geoserver/wms", "http://sample.server/geoserver/wms"]
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="wms"
                 options={options} map={map}/>, document.getElementById("container"));


        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
        expect(map.getLayers().item(0).getSource().urls.length).toBe(2);
    });

    it('creates a graticule layer for openlayers map', () => {
        var options = {
            "visibility": true
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="graticule"
                 options={options} map={map}/>, document.getElementById("container"));


        expect(layer).toExist();
        expect(layer.layer).toExist();

        expect(layer.layer.detached).toBe(true);

        layer.layer.remove();
    });

    it('creates a google layer for openlayers map', () => {
        var google = {
            maps: {
                MapTypeId: {
                    HYBRID: 'hybrid',
                    SATELLITE: 'satellite',
                    ROADMAP: 'roadmap',
                    TERRAIN: 'terrain'
                },
                Map: function() {
                    this.setMapTypeId = function() {};
                    this.setCenter = function() {};
                    this.setZoom = function() {};
                    this.setTilt = function() {};
                },
                LatLng: function() {

                }
            }
        };
        var options = {
            "type": "google",
            "name": "ROADMAP",
            "visibility": true
        };
        window.google = google;

        // create layers
        let layer = ReactDOM.render(
            <OpenlayersLayer type="google" options={options} map={map} mapId="map"/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        // google maps does not create a real ol layer, it is just injecting a gmaps api layer into DOM
        expect(map.getLayers().getLength()).toBe(0);
    });

    it('creates and overlay layer for openlayers map', () => {
        let container = document.createElement('div');
        container.id = 'ovcontainer';
        document.body.appendChild(container);

        let element = document.createElement('div');
        element.id = 'overlay-1';
        document.body.appendChild(element);

        let options = {
            id: 'overlay-1',
            position: [13, 43]
        };
        // create layers
        let layer = ReactDOM.render(
            <OpenlayersLayer type="overlay"
                 options={options} map={map}/>, document.getElementById('ovcontainer'));

        expect(layer).toExist();

        expect(document.getElementById('overlay-1-overlay')).toExist();
    });

    it('creates and overlay layer for openlayers map with close support', () => {
        let container = document.createElement('div');
        container.id = 'ovcontainer';
        document.body.appendChild(container);

        let element = document.createElement('div');
        element.id = 'overlay-1';
        let closeElement = document.createElement('div');
        closeElement.className = 'close';
        element.appendChild(closeElement);
        document.body.appendChild(element);
        let closed = false;
        let options = {
            id: 'overlay-1',
            position: [13, 43],
            onClose: () => {
                closed = true;
            }
        };
        // create layers
        let layer = ReactDOM.render(
            <OpenlayersLayer type="overlay"
                 options={options} map={map}/>, document.getElementById('ovcontainer'));

        expect(layer).toExist();
        const overlayElement = document.getElementById('overlay-1-overlay');
        expect(overlayElement).toExist();
        const close = overlayElement.getElementsByClassName('close')[0];
        close.click();
        expect(closed).toBe(true);
    });

    it('creates and overlay layer for openlayers map with no data-reactid attributes', () => {
        let container = document.createElement('div');
        container.id = 'ovcontainer';
        document.body.appendChild(container);

        let element = document.createElement('div');
        element.id = 'overlay-1';
        let closeElement = document.createElement('div');
        closeElement.className = 'close';
        element.appendChild(closeElement);
        document.body.appendChild(element);
        let options = {
            id: 'overlay-1',
            position: [13, 43]
        };
        // create layers
        let layer = ReactDOM.render(
            <OpenlayersLayer type="overlay"
                 options={options} map={map}/>, document.getElementById('ovcontainer'));

        expect(layer).toExist();
        const overlayElement = document.getElementById('overlay-1-overlay');
        expect(overlayElement.getAttribute('data-reactid')).toNotExist();
        const close = overlayElement.getElementsByClassName('close')[0];
        expect(close.getAttribute('data-reactid')).toNotExist();
    });

    it('creates a vector layer for openlayers map', () => {
        var options = {
            crs: 'EPSG:4326',
            features: {
              'type': 'FeatureCollection',
              'crs': {
                'type': 'name',
                'properties': {
                  'name': 'EPSG:4326'
                }
              },
              'features': [
                  {
                      'type': 'Feature',
                      'geometry': {
                          'type': 'Polygon',
                          'coordinates': [[
                              [13, 43],
                              [15, 43],
                              [15, 44],
                              [13, 44]
                          ]]
                      }
                  }
              ]
          }
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="vector"
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
    });

    it('creates a vector layer specifying the feature CRS for openlayers map', () => {
        var options = {
            crs: 'EPSG:4326',
            features: {
              'type': 'FeatureCollection',
              'crs': {
                'type': 'name',
                'properties': {
                  'name': 'EPSG:4326'
                }
              },
              'featureCrs': 'EPSG:3857',
              'features': [
                  {
                      'type': 'Feature',
                      'geometry': {
                          'type': 'Polygon',
                          'coordinates': [[
                              [1447153.3803125600, 5311971.8469454700],
                              [1669792.3618991000, 5311971.8469454700],
                              [1669792.3618991000, 5465442.1833227500],
                              [1447153.3803125600, 5465442.1833227500]
                          ]]
                      }
                  }
              ]
          }
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="vector"
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
    });

    it('creates a vector layer with a given marker style', () => {
        var options = {
            styleName: "marker",
            style: {
                iconUrl: "test",
                shadowUrl: "test"
            },
            crs: 'EPSG:4326',
            features: {
              'type': 'FeatureCollection',
              'crs': {
                'type': 'name',
                'properties': {
                  'name': 'EPSG:4326'
                }
              },
              'features': [
                  {
                      'type': 'Feature',
                      'geometry': {
                          'type': 'Point',
                          'coordinates': [13, 44]
                      }
                  },
                  {
                      'type': 'Feature',
                      'geometry': {
                          'type': 'Polygon',
                          'coordinates': [[
                              [13, 43],
                              [15, 43],
                              [15, 44],
                              [13, 44]
                          ]]
                      }
                  }
              ]
          }
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="vector"
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
    });

    it('creates a vector layer with a given point style', () => {
        var options = {
            style: {
                type: "Point",
                stroke: {
                    color: "blue",
                    width: 1
                },
                fill: {
                    color: "blue"
                },
                radius: 4
            },
            crs: 'EPSG:4326',
            features: {
              'type': 'FeatureCollection',
              'crs': {
                'type': 'name',
                'properties': {
                  'name': 'EPSG:4326'
                }
              },
              'features': [
                  {
                      'type': 'Feature',
                      'geometry': {
                          'type': 'Point',
                          'coordinates': [13, 44]
                      }
                  }
              ]
          }
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="vector"
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
    });

    it('vector layer with a given polygon style', () => {
        var options = {
            styleName: "Polygon",
            crs: 'EPSG:4326',
            features: {
              'type': 'FeatureCollection',
              'crs': {
                'type': 'name',
                'properties': {
                  'name': 'EPSG:4326'
                }
              },
              'features': [
                  {
                      'type': 'Feature',
                      'geometry': {
                          'type': 'Polygon',
                          'coordinates': [[
                              [13, 43],
                              [15, 43],
                              [15, 44],
                              [13, 44]
                          ]]
                      }
                  }
              ]
          }
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="vector"
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
    });

    it('change layer visibility for Google Layer', () => {
        var google = {
            maps: {
                MapTypeId: {
                    HYBRID: 'hybrid',
                    SATELLITE: 'satellite',
                    ROADMAP: 'roadmap',
                    TERRAIN: 'terrain'
                },
                Map: function() {
                    this.setMapTypeId = function() {};
                    this.setCenter = function() {};
                    this.setZoom = function() {};
                    this.setTilt = function() {};
                },
                LatLng: function() {

                }
            }
        };
        var options = {
            "type": "google",
            "name": "ROADMAP",
            "visibility": true
        };
        window.google = google;

        // create layers
        let layer = ReactDOM.render(
            <OpenlayersLayer type="google" options={options} map={map} mapId="map"/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        // google maps does not create a real ol layer, it is just injecting a gmaps api layer into DOM
        expect(map.getLayers().getLength()).toBe(0);
        let div = document.getElementById("mapgmaps");
        expect(div).toExist();

        // if only one layer for google exists, the div will be hidden
        let newOpts = assign({}, options, {visibility: false});
        layer = ReactDOM.render(
            <OpenlayersLayer type="google" options={newOpts} map={map} mapId="map"/>, document.getElementById("container"));
        expect(div.style.visibility).toBe('hidden');
    });

    it('rotates google layer when ol map is', () => {
        var google = {
            maps: {
                MapTypeId: {
                    HYBRID: 'hybrid',
                    SATELLITE: 'satellite',
                    ROADMAP: 'roadmap',
                    TERRAIN: 'terrain'
                },
                Map: function() {
                    this.setMapTypeId = function() {};
                    this.setCenter = function() {};
                    this.setZoom = function() {};
                    this.setTilt = function() {};
                },
                LatLng: function() {

                },
                event: {
                    trigger() {}
                }
            }
        };
        var options = {
            "type": "google",
            "name": "ROADMAP",
            "visibility": true
        };
        window.google = google;

        // create layers
        let layer = ReactDOM.render(
            <OpenlayersLayer type="google" options={options} map={map} mapId="map"/>, document.getElementById("container"));

        expect(layer).toExist();
        map.getView().setRotation(Math.PI / 2.0);

        let viewport = map.getViewport();
        viewport.dispatchEvent(new MouseEvent('mousedown'));
        viewport.dispatchEvent(new MouseEvent('mousemove'));
        viewport.dispatchEvent(new MouseEvent('mouseup'));

        let dom = document.getElementById("mapgmaps");
        expect(dom).toExist();
        expect(dom.style.transform).toBe('rotate(90deg)');
    });

    it('creates a bing layer for openlayers map', () => {
        var options = {
            "type": "bing",
            "title": "Bing Aerial",
            "name": "Aerial",
            "group": "background"
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="bing" options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
    });

    it('change a bing layer visibility', () => {
        var options = {
            "type": "bing",
            "title": "Bing Aerial",
            "name": "Aerial",
            "group": "background"
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="bing" options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        expect(layer.layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);
        expect(layer.layer.getVisible()).toBe(true);
        layer = ReactDOM.render(
            <OpenlayersLayer type="bing" options={{
                "type": "bing",
                "title": "Bing Aerial",
                "name": "Aerial",
                "group": "background",
                "visibility": true
            }} map={map}/>, document.getElementById("container"));
        expect(map.getLayers().getLength()).toBe(1);
        expect(layer.layer.getVisible()).toBe(true);
        layer = ReactDOM.render(
            <OpenlayersLayer type="bing" options={{
                "type": "bing",
                "title": "Bing Aerial",
                "name": "Aerial",
                "group": "background",
                "visibility": false
            }} map={map}/>, document.getElementById("container"));
        expect(map.getLayers().getLength()).toBe(1);
        expect(layer.layer.getVisible()).toBe(false);

    });

    it('creates a mapquest layer for openlayers map', () => {
        var options = {
            "type": "mapquest",
            "title": "MapQuest",
            "name": "osm",
            "group": "background"
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="mapquest" options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        // MapQuest is not supported on Openlayers
        expect(map.getLayers().getLength()).toBe(0);
    });

    it('changes wms layer opacity', () => {
        var options = {
            "type": "wms",
            "visibility": true,
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png",
            "opacity": 1.0,
            "url": "http://sample.server/geoserver/wms"
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="wms"
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);

        expect(layer.layer.getOpacity()).toBe(1.0);

        layer = ReactDOM.render(
            <OpenlayersLayer type="wms"
                 options={assign({}, options, {opacity: 0.5})} map={map}/>, document.getElementById("container"));

        expect(layer.layer.getOpacity()).toBe(0.5);
    });

    it('respects layer ordering', () => {
        var options = {
            "type": "wms",
            "visibility": true,
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png",
            "opacity": 1.0,
            "url": "http://sample.server/geoserver/wms"
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="wms" position={10}
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);

        expect(layer.layer.getZIndex()).toBe(10);

        layer = ReactDOM.render(
            <OpenlayersLayer type="wms" position={2}
                 options={options} map={map}/>, document.getElementById("container"));
        expect(layer.layer.getZIndex()).toBe(2);
    });

    it('changes wms params', () => {
        var options = {
            "type": "wms",
            "visibility": true,
            "name": "nurc:Arc_Sample",
            "group": "Meteo",
            "format": "image/png",
            "opacity": 1.0,
            "url": "http://sample.server/geoserver/wms",
            "params": {
                "cql_filter": "INCLUDE"
            }
        };
        // create layers
        var layer = ReactDOM.render(
            <OpenlayersLayer type="wms" observables={["cql_filter"]}
                 options={options} map={map}/>, document.getElementById("container"));

        expect(layer).toExist();
        // count layers
        expect(map.getLayers().getLength()).toBe(1);

        expect(layer.layer.getSource()).toExist();
        expect(layer.layer.getSource().getParams()).toExist();
        expect(layer.layer.getSource().getParams().cql_filter).toBe("INCLUDE");

        layer = ReactDOM.render(
            <OpenlayersLayer type="wms" observables={["cql_filter"]}
                 options={assign({}, options, {params: {cql_filter: "EXCLUDE"}})} map={map}/>, document.getElementById("container"));
        expect(layer.layer.getSource().getParams().cql_filter).toBe("EXCLUDE");
    });
});
