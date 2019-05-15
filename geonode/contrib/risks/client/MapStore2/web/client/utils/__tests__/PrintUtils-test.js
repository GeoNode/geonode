/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const expect = require('expect');
const PrintUtils = require('../PrintUtils');

const layer = {
    url: "http://mygeoserver",
    name: "my:layer",
    type: "wms",
    params: {myparam: "myvalue"}
};

const vectorLayer = {
  "type": "vector",
  "visibility": true,
  "group": "Local shape",
  "id": "web2014all_mv__14",
  "name": "web2014all_mv",
  "hideLoading": true,
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [
          -112.50042920000001,
          42.22829164089942
        ]
      },
      "properties": {
        "serial_num": "12C324776"
      },
      "id": 0
    }
  ],
  "style": {
    "weight": 3,
    "radius": 10,
    "opacity": 1,
    "fillOpacity": 0.1,
    "color": "rgb(0, 0, 255)",
    "fillColor": "rgb(0, 0, 255)"
  }
};
const mapFishVectorLayer = {
   "type": "Vector",
   "name": "web2014all_mv",
   "opacity": 1,
   "styleProperty": "ms_style",
   "styles": {
      "1": {
         "fillColor": "rgb(0, 0, 255)",
         "fillOpacity": 0.1,
         "pointRadius": 10,
         "strokeColor": "rgb(0, 0, 255)",
         "strokeOpacity": 1,
         "strokeWidth": 3
      }
   },
   "geoJson": {
      "type": "FeatureCollection",
      "features": [
         {
            "type": "Feature",
            "geometry": {
               "type": "Point",
               "coordinates": [
                  -12523490.492568726,
                  5195238.005360028
               ]
            },
            "properties": {
               "serial_num": "12C324776",
               "ms_style": 1
            },
            "id": 0
         }
      ]
   }
};
describe('PrintUtils', () => {

    it('custom params are applied to wms layers', () => {

        const specs = PrintUtils.getMapfishLayersSpecification([layer], {}, 'map');
        expect(specs).toExist();
        expect(specs.length).toBe(1);
        expect(specs[0].customParams.myparam).toExist();
        expect(specs[0].customParams.myparam).toBe("myvalue");
    });
    it('vector layer generation for print', () => {
        const specs = PrintUtils.getMapfishLayersSpecification([vectorLayer], {projection: "EPSG:3857"}, 'map');
        expect(specs).toExist();
        expect(specs.length).toBe(1);
        expect(specs[0].geoJson.features[0].geometry.coordinates[0], mapFishVectorLayer).toBe(mapFishVectorLayer.geoJson.features[0].geometry.coordinates[0]);
    });
    it('vector layer default point style', () => {
        const style = PrintUtils.getOlDefaultStyle({features: [{geometry: {type: "Point"}}]});
        expect(style).toExist();
        expect(style.pointRadius).toBe(5);
    });
    it('vector layer default marker style', () => {
        const style = PrintUtils.getOlDefaultStyle({styleName: "marker", features: [{geometry: {type: "Point"}}]});
        expect(style).toExist();
        expect(style.externalGraphic).toExist();
    });
    it('vector layer default polygon style', () => {
        const style = PrintUtils.getOlDefaultStyle({features: [{geometry: {type: "Polygon"}}]});
        expect(style).toExist();
        expect(style.strokeWidth).toBe(3);

    });
    it('vector layer default line style', () => {
        const style = PrintUtils.getOlDefaultStyle({features: [{geometry: {type: "LineString"}}]});
        expect(style).toExist();
        expect(style.strokeWidth).toBe(3);
    });
});
