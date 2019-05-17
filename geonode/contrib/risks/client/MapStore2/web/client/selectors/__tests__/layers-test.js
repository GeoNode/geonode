/**
* Copyright 2016, GeoSolutions Sas.
* All rights reserved.
*
* This source code is licensed under the BSD-style license found in the
* LICENSE file in the root directory of this source tree.
*/

const expect = require('expect');
const {layersSelector, layerSelectorWithMarkers, groupsSelector} = require('../layers');

describe('Test layers selectors', () => {
    it('test layersSelector from config', () => {
        const props = layersSelector({config: {layers: [{type: "osm"}]}});

        expect(props.length).toBe(1);
        expect(props[0].type).toBe("osm");
    });

    it('test layersSelector from layers', () => {
        const props = layersSelector({layers: [{type: "osm"}]});

        expect(props.length).toBe(1);
        expect(props[0].type).toBe("osm");
    });

    it('test layersSelector from layers flat', () => {
        const props = layersSelector({layers: {flat: [{type: "osm"}]}});

        expect(props.length).toBe(1);
        expect(props[0].type).toBe("osm");
    });

    it('test layerSelectorWithMarkers with no markers', () => {
        const props = layerSelectorWithMarkers({config: {layers: [{type: "osm"}]}});

        expect(props.length).toBe(1);
        expect(props[0].type).toBe("osm");
    });

    it('test layerSelectorWithMarkers with a marker', () => {
        const props = layerSelectorWithMarkers({config: {layers: [{type: "osm"}]}, mapInfo: {
            showMarker: true,
            clickPoint: {
                latlng: {lat: 45, lng: 43}
            }
        }});

        expect(props.length).toBe(2);
        expect(props[1].type).toBe("vector");
    });
    it('test layerSelectorWithMarkers with geocoder marker as lat lon', () => {
        const props = layerSelectorWithMarkers({config: {layers: [{type: "osm"}]}, search: {
            markerPosition: {
                lat: 0,
                lng: 0
            }
        }});
        expect(props.length).toBe(2);
        expect(props[1].type).toBe("vector");
    });
    it('test layerSelectorWithMarkers with geocoder marker as Point', () => {
        const props = layerSelectorWithMarkers({config: {layers: [{type: "osm"}]}, search: {
            markerPosition: {
                type: "Feature",
                geometry: {
                    type: "Point",
                    coordinates: [0, 0]
                }
            }
        }});
        expect(props.length).toBe(2);
        expect(props[1].type).toBe("vector");
    });
    it('test layerSelectorWithMarkers with geocoder marker as Polygon', () => {
        const props = layerSelectorWithMarkers({config: {layers: [{type: "osm"}]}, search: {
            markerPosition: {
                "type": "Feature",
                 "geometry": {
                   "type": "Polygon",
                   "coordinates": [
                     [ [100.0, 0.0], [101.0, 0.0], [101.0, 1.0],
                       [100.0, 1.0], [100.0, 0.0] ]
                     ]
                 },
                 "properties": {
                   "prop0": "value0"
                 }
            }
        }});
        expect(props.length).toBe(2);
        expect(props[1].type).toBe("vector");
    });

    it('test groupsSelector from layers flat one group', () => {
        const props = groupsSelector({layers: {
            flat: [{type: "osm", id: "layer1", group: "group1"}, {type: "wms", id: "layer2", group: "group1"}],
            groups: [{name: "group1", nodes: ["layer1", "layer2"]}]
        }});

        expect(props.length).toBe(1);
        expect(props[0].nodes.length).toBe(2);
        expect(props[0].nodes[0]).toNotBeA('string');
    });

    it('test groupsSelector from layers flat more groups', () => {
        const props = groupsSelector({layers: {
            flat: [{type: "osm", id: "layer1", group: "group1"}, {type: "wms", id: "layer2", group: "group2"}],
            groups: [
                {name: "group1", nodes: ["layer1"]},
                {name: "group2", nodes: ["layer2"]}
            ]
        }});

        expect(props.length).toBe(2);
        expect(props[0].nodes.length).toBe(1);
        expect(props[1].nodes.length).toBe(1);
        expect(props[0].nodes[0]).toNotBeA('string');
        expect(props[1].nodes[0]).toNotBeA('string');
    });
});
