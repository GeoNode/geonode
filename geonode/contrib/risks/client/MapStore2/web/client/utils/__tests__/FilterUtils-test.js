/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');
var FilterUtils = require('../FilterUtils');

describe('FilterUtils', () => {
    it('Calculate OGC filter', () => {
        let filterObj = {
            filterFields: [{
                attribute: "attribute1",
                groupId: 1,
                exception: null,
                operator: "=",
                rowId: "1",
                type: "list",
                value: "value1"
            }, {
                attribute: "attribute2",
                exception: null,
                groupId: 1,
                operator: "=",
                rowId: "2",
                type: "list",
                value: "value2"
            },
            {
                attribute: "attribute3",
                exception: null,
                groupId: 1,
                operator: "=",
                rowId: "3",
                type: "number",
                value: "value1"
            },
            {
                attribute: "attribute4",
                exception: null,
                operator: "><",
                groupId: 1,
                rowId: "4",
                type: "number",
                value: {lowBound: 10, upBound: 20}
            },
            {
                attribute: "attribute5",
                exception: null,
                operator: "isNull",
                groupId: 1,
                rowId: "5",
                type: "string",
                value: ''
            },
            {
                attribute: "attribute5",
                exception: null,
                operator: "ilike",
                groupId: 1,
                rowId: "6",
                type: "string",
                value: 'pa'
            }],
            groupFields: [{
                id: 1,
                index: 0,
                logic: "OR"
            }],
            spatialField: {
                groupId: 1,
                attribute: "the_geom",
                geometry: {
                    center: [1, 1],
                    coordinates: [
                        [1, 2],
                        [2, 3],
                        [3, 4],
                        [4, 5],
                        [5, 6]
                    ],
                    extent: [
                        1, 2, 3, 4, 5
                    ],
                    projection: "EPSG:4326",
                    radius: 1,
                    type: "Polygon"
                },
                method: "BBOX",
                operation: "INTERSECTS"
            }
        };

        let filter = FilterUtils.toOGCFilter("ft_name_test", filterObj);
        expect(filter).toExist();
    });

    it('Calculate CQL filter', () => {
        let filterObj = {
            filterFields: [{
                groupId: 1,
                attribute: "attribute1",
                exception: null,
                operator: "=",
                rowId: "1",
                type: "list",
                value: "value1"
            }, {
                groupId: 1,
                attribute: "attribute2",
                exception: null,
                operator: "=",
                rowId: "2",
                type: "list",
                value: "value2"
            },
            {
                groupId: 1,
                attribute: "attribute3",
                exception: null,
                operator: "=",
                rowId: "3",
                type: "number",
                value: "value1"
            },
            {
                groupId: 1,
                attribute: "attribute4",
                exception: null,
                operator: "><",
                rowId: "4",
                type: "number",
                value: {lowBound: 10, upBound: 20}
            },
            {
                attribute: "attribute5",
                exception: null,
                operator: "isNull",
                groupId: 1,
                rowId: "5",
                type: "string",
                value: ''
            },
            {
                attribute: "attribute5",
                exception: null,
                operator: "ilike",
                groupId: 1,
                rowId: "6",
                type: "string",
                value: 'pa'
            }],
            groupFields: [{
                id: 1,
                index: 0,
                logic: "OR"
            }],
            spatialField: {
                groupId: 1,
                attribute: "the_geom",
                geometry: {
                    center: [1, 1],
                    coordinates: [
                        [1, 2],
                        [2, 3],
                        [3, 4],
                        [4, 5],
                        [5, 6]
                    ],
                    extent: [
                        1, 2, 3, 4, 5
                    ],
                    projection: "EPSG:4326",
                    radius: 1,
                    type: "Polygon"
                },
                method: "BBOX",
                operation: "INTERSECTS"
            }
        };

        let filter = FilterUtils.toCQLFilter(filterObj);
        expect(filter).toExist();
    });

    it('Check for pagination wfs 1.1.0', () => {
        let filterObj = {
            pagination: {
                startIndex: 1,
                maxFeatures: 20
            },
            spatialField: {
                attribute: "the_geom",
                geometry: {
                    center: [1, 1],
                    coordinates: [
                        [1, 2],
                        [2, 3],
                        [3, 4],
                        [4, 5],
                        [5, 6]
                    ],
                    extent: [
                        1, 2, 3, 4, 5
                    ],
                    projection: "EPSG:4326",
                    radius: 1,
                    type: "Polygon"
                },
                method: "BBOX",
                operation: "INTERSECTS"
            }
        };

        let filter = FilterUtils.toOGCFilter("ft_name_test", filterObj, "1.1.0");
        expect(filter.indexOf('maxFeatures="20"') !== -1).toBe(true);
        expect(filter.indexOf('startIndex="1"') !== -1).toBe(true);
    });

    it('Check for pagination wfs 2.0', () => {
        let filterObj = {
            pagination: {
                startIndex: 1,
                maxFeatures: 20
            },
            spatialField: {
                attribute: "the_geom",
                geometry: {
                    center: [1, 1],
                    coordinates: [
                        [1, 2],
                        [2, 3],
                        [3, 4],
                        [4, 5],
                        [5, 6]
                    ],
                    extent: [
                        1, 2, 3, 4, 5
                    ],
                    projection: "EPSG:4326",
                    radius: 1,
                    type: "Polygon"
                },
                method: "BBOX",
                operation: "INTERSECTS"
            }
        };

        let filter = FilterUtils.toOGCFilter("ft_name_test", filterObj);
        expect(filter.indexOf('count="20"') !== -1).toBe(true);
        expect(filter.indexOf('startIndex="1"') !== -1).toBe(true);
    });

    it('Check for no pagination', () => {
        let filterObj = {
            spatialField: {
                attribute: "the_geom",
                geometry: {
                    center: [1, 1],
                    coordinates: [
                        [1, 2],
                        [2, 3],
                        [3, 4],
                        [4, 5],
                        [5, 6]
                    ],
                    extent: [
                        1, 2, 3, 4, 5
                    ],
                    projection: "EPSG:4326",
                    radius: 1,
                    type: "Polygon"
                },
                method: "BBOX",
                operation: "INTERSECTS"
            }
        };

        let filter = FilterUtils.toOGCFilter("ft_name_test", filterObj);
        expect(filter.indexOf('count="20"') !== -1).toBe(false);
        expect(filter.indexOf('maxFeatures="20"') !== -1).toBe(false);
        expect(filter.indexOf('startIndex="1"') !== -1).toBe(false);
    });
    it('Check SimpleFilterField ogc', () => {
        let filterObj = {
            simpleFilterFields: [{
                    "fieldId": 1,
                    "label": "Highway System",
                    "attribute": "highway_system",
                    "multivalue": false,
                    "values": ["state"],
                    "optionsValues": ["local", "state"],
                    "optionsLabels": {
                        "local": "Local",
                        "state": "State"
                    },
                    "type": "list",
                    "operator": "=",
                    "required": true,
                    "sort": "ASC",
                    "defaultExpanded": true,
                    "collapsible": true
                    }]
        };
        let expected = '<wfs:GetFeature service="WFS" version="2.0" xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:fes="http://www.opengis.net/fes/2.0" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/wfs/2.0 http://schemas.opengis.net/wfs/2.0/wfs.xsd http://www.opengis.net/gml/3.2 http://schemas.opengis.net/gml/3.2.1/gml.xsd"><wfs:Query typeNames="ft_name_test" srsName="EPSG:4326"><fes:Filter><fes:And><fes:Or><fes:PropertyIsEqualTo><fes:ValueReference>highway_system</fes:ValueReference><fes:Literal>state</fes:Literal></fes:PropertyIsEqualTo></fes:Or></fes:And></fes:Filter></wfs:Query></wfs:GetFeature>';
        let filter = FilterUtils.toOGCFilter("ft_name_test", filterObj);
        expect(filter).toEqual(expected);
    });
    it('Check SpatialFilterField ogc 1.0.0 Polygon', () => {
        let filterObj = {
            spatialField: {
                    "operation": "INTERSECTS",
                    "attribute": "geometry",
                    "geometry": {
                        "type": "Polygon",
                        "projection": "EPSG:4326",
                        "coordinates": [[[1, 1], [1, 2], [2, 2], [2, 1], [1, 1]]]
                    }
                }
        };
        let expected = '<wfs:GetFeature service="WFS" version="1.0.0" outputFormat="GML2" xmlns:gml="http://www.opengis.net/gml" xmlns:wfs="http://www.opengis.net/wfs" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.0.0/WFS-basic.xsd"><wfs:Query typeName="ft_name_test" srsName="EPSG:4326"><ogc:Filter><ogc:Intersects><ogc:PropertyName>geometry</ogc:PropertyName><gml:Polygon srsName="EPSG:4326"><gml:outerBoundaryIs><gml:LinearRing><gml:coordinates>1,1 1,2 2,2 2,1 1,1</gml:coordinates></gml:LinearRing></gml:outerBoundaryIs></gml:Polygon></ogc:Intersects></ogc:Filter></wfs:Query></wfs:GetFeature>';
        let filter = FilterUtils.toOGCFilter("ft_name_test", filterObj, "1.0.0");
        expect(filter).toEqual(expected);
    });
    it('Check SpatialFilterField ogc 1.0.0 Point', () => {
        let filterObj = {
            spatialField: {
                    "operation": "INTERSECTS",
                    "attribute": "geometry",
                    "geometry": {
                        "type": "Point",
                        "projection": "EPSG:4326",
                        "coordinates": [[[1, 1]]]
                    }
                }
        };
        let expected = '<wfs:GetFeature service="WFS" version="1.0.0" outputFormat="GML2" xmlns:gml="http://www.opengis.net/gml" xmlns:wfs="http://www.opengis.net/wfs" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.0.0/WFS-basic.xsd"><wfs:Query typeName="ft_name_test" srsName="EPSG:4326"><ogc:Filter><ogc:Intersects><ogc:PropertyName>geometry</ogc:PropertyName><gml:Point srsDimension="2" srsName="EPSG:4326"><gml:coord><X>1</X><Y>1</Y></gml:coord></gml:Point></ogc:Intersects></ogc:Filter></wfs:Query></wfs:GetFeature>';
        let filter = FilterUtils.toOGCFilter("ft_name_test", filterObj, "1.0.0");
        expect(filter).toEqual(expected);
    });
    it('Check SpatialFilterField normalizeVersion', () => {
        let filterObj = {
            spatialField: {
                    "operation": "INTERSECTS",
                    "attribute": "geometry",
                    "geometry": {
                        "type": "Point",
                        "projection": "EPSG:4326",
                        "coordinates": [[[1, 1]]]
                    }
                }
        };
        let expected = '<wfs:GetFeature service="WFS" version="1.0.0" outputFormat="GML2" xmlns:gml="http://www.opengis.net/gml" xmlns:wfs="http://www.opengis.net/wfs" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.0.0/WFS-basic.xsd"><wfs:Query typeName="ft_name_test" srsName="EPSG:4326"><ogc:Filter><ogc:Intersects><ogc:PropertyName>geometry</ogc:PropertyName><gml:Point srsDimension="2" srsName="EPSG:4326"><gml:coord><X>1</X><Y>1</Y></gml:coord></gml:Point></ogc:Intersects></ogc:Filter></wfs:Query></wfs:GetFeature>';
        let filter = FilterUtils.toOGCFilter("ft_name_test", filterObj, "1.0");
        expect(filter).toEqual(expected);
    });
    it('Check SpatialFilterField ogc 1.1.0 Polygon', () => {
        let filterObj = {
            spatialField: {
                    "attribute": "geometry",
                    "operation": "INTERSECTS",
                    "geometry": {
                        "type": "Polygon",
                        "projection": "EPSG:4326",
                        "coordinates": [[[1, 1], [1, 2], [2, 2], [2, 1], [1, 1]]]
                    }
                }
        };
        let expected = '<wfs:GetFeature service="WFS" version="1.1.0" xmlns:gml="http://www.opengis.net/gml" xmlns:wfs="http://www.opengis.net/wfs" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd"><wfs:Query typeName="ft_name_test" srsName="EPSG:4326"><ogc:Filter><ogc:Intersects><ogc:PropertyName>geometry</ogc:PropertyName><gml:Polygon srsName="EPSG:4326"><gml:exterior><gml:LinearRing><gml:posList>1 1 1 2 2 2 2 1 1 1</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></ogc:Intersects></ogc:Filter></wfs:Query></wfs:GetFeature>';
        let filter = FilterUtils.toOGCFilter("ft_name_test", filterObj, "1.1.0");
        expect(filter).toEqual(expected);
    });
    it('Check SpatialFilterField ogc 1.1.0 Point', () => {
        let filterObj = {
            spatialField: {
                    "operation": "INTERSECTS",
                    "attribute": "geometry",
                    "geometry": {
                        "type": "Point",
                        "projection": "EPSG:4326",
                        "coordinates": [[[1, 1]]]
                    }
                }
        };
        let expected = '<wfs:GetFeature service="WFS" version="1.1.0" xmlns:gml="http://www.opengis.net/gml" xmlns:wfs="http://www.opengis.net/wfs" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd"><wfs:Query typeName="ft_name_test" srsName="EPSG:4326"><ogc:Filter><ogc:Intersects><ogc:PropertyName>geometry</ogc:PropertyName><gml:Point srsDimension="2" srsName="EPSG:4326"><gml:pos>1 1</gml:pos></gml:Point></ogc:Intersects></ogc:Filter></wfs:Query></wfs:GetFeature>';
        let filter = FilterUtils.toOGCFilter("ft_name_test", filterObj, "1.1.0");
        expect(filter).toEqual(expected);
    });
    it('Check SpatialFilterField ogc 2.0 Point', () => {
        let filterObj = {
            spatialField: {
                    "operation": "INTERSECTS",
                    "attribute": "geometry",
                    "geometry": {
                        "type": "Point",
                        "projection": "EPSG:4326",
                        "coordinates": [[[1, 1]]]
                    }
                }
        };
        let expected = '<wfs:GetFeature service="WFS" version="2.0" xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:fes="http://www.opengis.net/fes/2.0" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/wfs/2.0 http://schemas.opengis.net/wfs/2.0/wfs.xsd http://www.opengis.net/gml/3.2 http://schemas.opengis.net/gml/3.2.1/gml.xsd"><wfs:Query typeNames="ft_name_test" srsName="EPSG:4326"><fes:Filter><fes:Intersects><fes:ValueReference>geometry</fes:ValueReference><gml:Point srsDimension="2" srsName="EPSG:4326"><gml:pos>1 1</gml:pos></gml:Point></fes:Intersects></fes:Filter></wfs:Query></wfs:GetFeature>';
        let filter = FilterUtils.toOGCFilter("ft_name_test", filterObj, "2.0");
        expect(filter).toEqual(expected);
    });
    it('Check SpatialFilterField ogc 2.0 Polygon', () => {
        let filterObj = {
            spatialField: {
                    "attribute": "geometry",
                    "operation": "INTERSECTS",
                    "geometry": {
                        "type": "Polygon",
                        "projection": "EPSG:4326",
                        "coordinates": [[[1, 1], [1, 2], [2, 2], [2, 1], [1, 1]]]
                    }
                }
        };
        let expected = '<wfs:GetFeature service="WFS" version="2.0" xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:fes="http://www.opengis.net/fes/2.0" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/wfs/2.0 http://schemas.opengis.net/wfs/2.0/wfs.xsd http://www.opengis.net/gml/3.2 http://schemas.opengis.net/gml/3.2.1/gml.xsd"><wfs:Query typeNames="ft_name_test" srsName="EPSG:4326"><fes:Filter><fes:Intersects><fes:ValueReference>geometry</fes:ValueReference><gml:Polygon srsName="EPSG:4326"><gml:exterior><gml:LinearRing><gml:posList>1 1 1 2 2 2 2 1 1 1</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></fes:Intersects></fes:Filter></wfs:Query></wfs:GetFeature>';
        let filter = FilterUtils.toOGCFilter("ft_name_test", filterObj, "2.0");
        expect(filter).toEqual(expected);
    });
    it('Check SpatialFilterField ogc default version is 2.0', () => {
        let filterObj = {
            spatialField: {
                    "operation": "INTERSECTS",
                    "attribute": "geometry",
                    "geometry": {
                        "type": "Point",
                        "projection": "EPSG:4326",
                        "coordinates": [[[1, 1]]]
                    }
                }
        };
        let expected = '<wfs:GetFeature service="WFS" version="2.0" xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:fes="http://www.opengis.net/fes/2.0" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/wfs/2.0 http://schemas.opengis.net/wfs/2.0/wfs.xsd http://www.opengis.net/gml/3.2 http://schemas.opengis.net/gml/3.2.1/gml.xsd"><wfs:Query typeNames="ft_name_test" srsName="EPSG:4326"><fes:Filter><fes:Intersects><fes:ValueReference>geometry</fes:ValueReference><gml:Point srsDimension="2" srsName="EPSG:4326"><gml:pos>1 1</gml:pos></gml:Point></fes:Intersects></fes:Filter></wfs:Query></wfs:GetFeature>';
        let filter = FilterUtils.toOGCFilter("ft_name_test", filterObj);
        expect(filter).toEqual(expected);
    });
    it('Check SpatialFilterField cql', () => {
        let filterObj = {
            simpleFilterFields: [{
                    "fieldId": 1,
                    "label": "Highway System",
                    "attribute": "highway_system",
                    "multivalue": false,
                    "values": ["state"],
                    "type": "list",
                    "operator": "=",
                    "optionsValues": ["local", "state"],
                    "optionsLabels": {
                        "local": "Local",
                        "state": "State"
                    },
                    "required": true,
                    "sort": "ASC",
                    "defaultExpanded": true,
                    "collapsible": true
                    }]
        };
        let expected = "((highway_system IN('state')))";
        let filter = FilterUtils.toCQLFilter(filterObj);
        expect(filter).toEqual(expected);
    });
    it('Check CrossLayerFilter segment generation', () => {
        let crossLayerFilterObj = {
           operation: "INTERSECTS",
           attribute: "roads_geom",
           collectGeometries: {queryCollection: {
               typeName: "regions",
               geometryName: "regions_geom",
               cqlFilter: "area > 10"
           }}
        };
        let expected = "<ogc:Intersects>"
         + '<ogc:PropertyName>roads_geom</ogc:PropertyName>'
         + '<ogc:Function name="collectGeometries">'
         + '<ogc:Function name="queryCollection">'
         + '<ogc:Literal>regions</ogc:Literal>'
         + '<ogc:Literal>regions_geom</ogc:Literal>'
         + '<ogc:Literal>area > 10</ogc:Literal>'
         + '</ogc:Function></ogc:Function>'
         + "</ogc:Intersects>";

        // this is a workarround for this issue : https://github.com/geosolutions-it/MapStore2/issues/1263
        // please remove when fixed
        FilterUtils.nsplaceholder = "ogc";
        FilterUtils.setOperatorsPlaceholders("{namespace}");

        let filter = FilterUtils.processOGCCrossLayerFilter(crossLayerFilterObj);
        expect(filter).toEqual(expected);
    });
});
