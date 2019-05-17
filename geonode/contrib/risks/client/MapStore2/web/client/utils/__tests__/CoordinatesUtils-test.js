/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');
var CoordinatesUtils = require('../CoordinatesUtils');
var Proj4js = require('proj4');

describe('CoordinatesUtils', () => {
    afterEach((done) => {
        document.body.innerHTML = '';

        setTimeout(done);
    });
    it('convert lat lon to mercator', () => {
        var point = [45, 13];

        var transformed = CoordinatesUtils.reproject(point, 'EPSG:4326', 'EPSG:900913');

        expect(transformed).toExist();
        expect(transformed.x).toExist();
        expect(transformed.y).toExist();
        expect(transformed.srs).toExist();

        expect(transformed.x).toNotBe(45);
        expect(transformed.y).toNotBe(13);
        expect(transformed.srs).toBe('EPSG:900913');
    });
    it('convert lat lon bbox to marcator bbox', () => {
        var bbox = [44, 12, 45, 13];
        var projbbox = CoordinatesUtils.reprojectBbox(bbox, 'EPSG:4326', 'EPSG:900913');

        expect(projbbox).toExist();
        expect(projbbox.length).toBe(4);
        for (let i = 0; i < 4; i++) {
            expect(projbbox[i]).toNotBe(bbox[i]);
        }
    });
    it('test getAvailableCRS', () => {
        const defs = Object.keys(Proj4js.defs);
        const toCheck = Object.keys(CoordinatesUtils.getAvailableCRS());

        toCheck.forEach(item => {
            expect(defs.indexOf(item) !== -1);
        });
    });
    it('test calculateAzimuth', () => {
        var point1 = [0, 0];
        var point2 = [1, 1];
        var proj = 'EPSG:900913';
        var azimuth = CoordinatesUtils.calculateAzimuth(point1, point2, proj);

        expect(azimuth.toFixed(2)).toBe('45.00');
    });
    it('test normalizeSRS', () => {
        expect(CoordinatesUtils.normalizeSRS('EPSG:900913')).toBe('EPSG:3857');
    });

    it('test normalizeSRS with allowedSRS', () => {
        expect(CoordinatesUtils.normalizeSRS('EPSG:900913', {'EPSG:900913': true})).toBe('EPSG:900913');
    });

    it('test getCompatibleSRS', () => {
        expect(CoordinatesUtils.getCompatibleSRS('EPSG:900913', {'EPSG:900913': true})).toBe('EPSG:900913');
        expect(CoordinatesUtils.getCompatibleSRS('EPSG:900913', {'EPSG:900913': true, 'EPSG:3857': true})).toBe('EPSG:900913');
        expect(CoordinatesUtils.getCompatibleSRS('EPSG:900913', {'EPSG:3857': true})).toBe('EPSG:3857');

        expect(CoordinatesUtils.getCompatibleSRS('EPSG:3857', {'EPSG:900913': true})).toBe('EPSG:900913');
        expect(CoordinatesUtils.getCompatibleSRS('EPSG:3857', {'EPSG:900913': true, 'EPSG:3857': true})).toBe('EPSG:3857');
        expect(CoordinatesUtils.getCompatibleSRS('EPSG:3857', {'EPSG:3857': true})).toBe('EPSG:3857');
    });
    it('test reprojectGeoJson', () => {
        const testPoint = {
            type: "FeatureCollection",
            features: [
               {
                  type: "Feature",
                  geometry: {
                     type: "Point",
                     coordinates: [
                        -112.50042920000001,
                        42.22829164089942
                     ]
                  },
                  properties: {
                     "serial_num": "12C324776"
                  },
                  id: 0
               }
            ]
        };
        const reprojectedTestPoint = CoordinatesUtils.reprojectGeoJson(testPoint, "EPSG:4326", "EPSG:900913");
        expect(reprojectedTestPoint).toExist();
        expect(reprojectedTestPoint.features).toExist();
        expect(reprojectedTestPoint.features[0]).toExist();
        expect(reprojectedTestPoint.features[0].type).toBe("Feature");
        expect(reprojectedTestPoint.features[0].geometry.type).toBe("Point");
        // approximate values should be the same
        expect(reprojectedTestPoint.features[0].geometry.coordinates[0].toFixed(4)).toBe((-12523490.492568726).toFixed(4));
        expect(reprojectedTestPoint.features[0].geometry.coordinates[1].toFixed(4)).toBe((5195238.005360028).toFixed(4));
    });

    it('test geojson extent', () => {
        let geojsonPoint = {
          "type": "Feature",
          "geometry": {
            "type": "Point",
            "coordinates": [125.6, 10.1]
          },
          "properties": {
            "name": "Dinagat Islands"
          }
        };
        expect(CoordinatesUtils.getGeoJSONExtent(geojsonPoint)[0] <= 125.6).toBe(true);
        expect(CoordinatesUtils.getGeoJSONExtent(geojsonPoint)[1] <= 10.1).toBe(true);
        expect(CoordinatesUtils.getGeoJSONExtent(geojsonPoint)[2] >= 125.6).toBe(true);
        expect(CoordinatesUtils.getGeoJSONExtent(geojsonPoint)[3] >= 10.1).toBe(true);
        let featureCollection = { "type": "FeatureCollection",
            "features": [
              { "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [102.0, 0.5]},
                "properties": {"prop0": "value0"}
              },
              { "type": "Feature",
                "geometry": {
                    "type": "GeometryCollection",
                    "geometries": [{"type": "Point", "coordinates": [102.0, 0.5]}]
                },
                "properties": {"prop0": "value0"}
              },
              { "type": "Feature",
                "geometry": {
                  "type": "LineString",
                  "coordinates": [
                    [102.0, 0.0], [103.0, 1.0], [104.0, 0.0], [105.0, 1.0]
                    ]
                  },
                "properties": {
                  "prop0": "value0",
                  "prop1": 0.0
                  }
                },
              { "type": "Feature",
                 "geometry": {
                   "type": "Polygon",
                   "coordinates": [
                     [ [100.0, 0.0], [101.0, 0.0], [101.0, 1.0],
                       [100.0, 1.0], [100.0, 0.0] ]
                     ]
                 },
                 "properties": {
                   "prop0": "value0",
                   "prop1": {"this": "that"}
                   }
                 }
               ]
        };
        expect(CoordinatesUtils.getGeoJSONExtent(featureCollection)[0]).toBe(100.0);
        expect(CoordinatesUtils.getGeoJSONExtent(featureCollection)[1]).toBe(0.0);
        expect(CoordinatesUtils.getGeoJSONExtent(featureCollection)[2]).toBe(105.0);
        expect(CoordinatesUtils.getGeoJSONExtent(featureCollection)[3]).toBe(1.0);
    });
});
