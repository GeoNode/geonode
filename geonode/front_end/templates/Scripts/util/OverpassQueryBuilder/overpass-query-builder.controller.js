(function () {
    appModule
        .controller('OverpassApiQueryBuilderController', OverpassApiQueryBuilderController);

    OverpassApiQueryBuilderController.$inject = ['$scope', '$modalInstance', 'mapService', '$http', '$compile'];

    function OverpassApiQueryBuilderController($scope, $modalInstance, mapService, $http, $compile) {
        var url = 'http://overpass-api.de/api/interpreter';
        $scope.queryStr = "node({{bbox}});out;";
        var vectorLayer;
        var boundingBox;
        var styles = {
            'amenity': {
                '.*': [
                    new ol.style.Style({
                        image: new ol.style.RegularShape({
                            fill: new ol.style.Fill({
                                color: 'red'
                            }),
                            stroke: new ol.style.Stroke({
                                color: 'black',
                                width: 2
                            }),
                            points: 4,
                            radius: 10,
                            radius2: 0,
                            angle: Math.PI / 2
                        })
                    })
                ]
            },
            'building': {
                '.*': [
                    new ol.style.Style({
                        zIndex: 100,
                        stroke: new ol.style.Stroke({
                            color: 'rgba(246, 99, 79, 1.0)',
                            width: 1
                        }),
                        fill: new ol.style.Fill({
                            color: 'rgba(246, 99, 79, 0.3)'
                        })
                    })
                ]
            },
            'highway': {
                'service': [
                    new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: 'rgba(255, 255, 255, 1.0)',
                            width: 2
                        })
                    })
                ],
                '.*': [
                    new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: 'rgba(255, 255, 255, 1.0)',
                            width: 3
                        })
                    })
                ]
            },
            'landuse': {
                'forest|grass|allotments': [
                    new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: 'rgba(140, 208, 95, 1.0)',
                            width: 1
                        }),
                        fill: new ol.style.Fill({
                            color: 'rgba(140, 208, 95, 0.3)'
                        })
                    })
                ]
            },
            'natural': {
                'tree': [
                    new ol.style.Style({
                        image: new ol.style.Circle({
                            radius: 2,
                            fill: new ol.style.Fill({
                                color: 'rgba(140, 208, 95, 1.0)'
                            }),
                            stroke: null
                        })
                    })
                ]
            }
        };
        var boxTopLeft, boxTopRight, boxBottomRight, boxBottomLeft;
        $scope.closeDialog = function () {
            $modalInstance.close();
        };

        function _Style(feature, resolution) {
            for (var key in styles) {
                var value = feature.get(key);
                if (value !== undefined) {
                    for (var regexp in styles[key]) {
                        if (new RegExp(regexp).test(value)) {
                            return styles[key][regexp];
                        }
                    }
                }
            }
            return null;
        }

        function _random(number) {
            return Math.round(Math.random() * number);
        }

        function _AddLayer(features) {
            var vectorSource = new ol.source.Vector({
                features: features
            });
            vectorLayer = new ol.layer.Vector({
                source: vectorSource,
                style: [
                    new ol.style.Style({
                        image: new ol.style.Circle({
                            fill: new ol.style.Fill({
                                color: 'rgba(' + _random(255) + ',' + _random(255) + ',' + _random(255) + ',' + 1.0 + ')'
                            }),
                            stroke: new ol.style.Stroke({
                                color: 'rgba(' + _random(255) + ',' + _random(255) + ',' + _random(255) + ',' + 0.3 + ')',
                                width: 2
                            }),
                            // points: 4,
                            radius: 10,
                            // radius2: 0,
                            // angle: Math.PI / 2
                        })
                    })
                ]
            });
            mapService.addVectorLayer(vectorLayer);
        }

        $scope.executeQuery = function (query) {
            if (vectorLayer) {
                mapService.removeVectorLayer(vectorLayer);
            }
            var extent = mapService.getMapExtent();
            var projection = mapService.getProjection();
            if (boundingBox){
                extent = ol.extent.boundingExtent([
                    boundingBox[0],
                    boundingBox[2]
                ]);
            }
            var epsg4326Extent =
                ol.proj.transformExtent(extent, projection, 'EPSG:4326');

            var param = query.split("{{bbox}}");
            param = '(' + param[0] +
                epsg4326Extent[1] + ',' + epsg4326Extent[0] + ',' +
                epsg4326Extent[3] + ',' + epsg4326Extent[2] +
                ');' + param[1];
            $http.post(url, param)
                .then(function (response) {
                    var features = new ol.format.OSMXML().readFeatures(response.data, {
                        featureProjection: projection
                    });
                    _AddLayer(features);
                });
        };
        var map = mapService.getMap();
        var dragFeature = null;
        var dragCoordinate = null;
        var dragCursor = 'pointer';
        var dragPrevCursor = null;


        var STROKE_WIDTH = 3,
            CIRCLE_RADIUS = 5;

        var FILL_COLOR = 'rgba(255, 255, 255, 0.5)',
            STROKE_COLOR = 'rgba(0, 60, 136, 0.8)';

        var lineStyle = new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: STROKE_COLOR,
                width: STROKE_WIDTH
            }),
            fill: new ol.style.Fill({
                color: FILL_COLOR
            })
        })


        var verticeStyle = new ol.style.Style({
            image: new ol.style.Circle({
                radius: CIRCLE_RADIUS,
                stroke: new ol.style.Stroke({
                    color: STROKE_COLOR,
                    width: STROKE_WIDTH
                }),
                fill: new ol.style.Fill({
                    color: FILL_COLOR
                })
            }),
            geometry: function (feature) {
                var coordinates = feature.getGeometry().getCoordinates();
                return new ol.geom.MultiPoint(coordinates[0]);
            }
        });

        var rectangularStyle = new ol.style.Style({
            image: new ol.style.RegularShape({
                points: 4,
                radius: 10,
                stroke: new ol.style.Stroke({
                    color: 'rgba(255, 0, 255, 1)',
                    width: STROKE_WIDTH
                }),
                fill: new ol.style.Fill({
                    color: FILL_COLOR
                })
            })
        });

        var features = new ol.Collection();
        features.on('add', function (event) {
            var feature = event.element;
            feature.set('id', 'bounding-box');
        });

        var vectorSource = new ol.source.Vector({
            features: features,
        });
        var featureOverlay = new ol.layer.Vector({
            source: vectorSource,
            style: [verticeStyle, lineStyle]
        })
        featureOverlay.setMap(map);

        function updateGeometry(feature, coordinate){
            boxTopLeft = [boxTopLeft[0], coordinate[1]];
            boxTopRight =  coordinate;
            boxBottomRight = [coordinate[0], boxBottomRight[1]];
            // boxBottomLeft =  [end[0], start[1]];

            var geometry = feature.getGeometry();
            geometry.setCoordinates([
                [boxTopLeft, boxBottomLeft, boxBottomRight , boxTopRight, boxTopLeft]
            ]);
        }
        function finEuclideanDistance(coord1, coord2){
            return Math.sqrt(Math.pow(coord1[0] - coord2[0], 2) + Math.pow(coord1[1] - coord2[1], 2));
        }
        var dragInteraction = new ol.interaction.Pointer({
            handleDownEvent: function (event) {
                var feature = map.forEachFeatureAtPixel(event.pixel,
                    function (feature, layer) {
                        return feature;
                    }
                );

                if (feature && feature.get('id') === 'bounding-box') {
                    dragCoordinate = event.coordinate;
                    // findMinDistance(dragCoordinate);
                    // updateGeometry(feature, dragCoordinate);
                    dragFeature = feature;
                    console.log(finEuclideanDistance(dragCoordinate, boxTopRight));
                    return true;
                }

                return false;
            },
            handleDragEvent: function (event) {
                var deltaX = event.coordinate[0] - dragCoordinate[0];
                var deltaY = event.coordinate[1] - dragCoordinate[1];

                var geometry = dragFeature.getGeometry();
                // geometry.translate(deltaX, deltaY);
                // geometry.setCoordinates()
                updateGeometry(dragFeature, event.coordinate);
                
                dragCoordinate[0] = event.coordinate[0];
                dragCoordinate[1] = event.coordinate[1];
            },
            handleMoveEvent: function (event) {
                if (dragCursor) {
                    var map = event.map;

                    var feature = map.forEachFeatureAtPixel(event.pixel,
                        function (feature, layer) {
                            return feature;
                        });

                    var element = event.map.getTargetElement();

                    if (feature) {
                        if (element.style.cursor != dragCursor) {
                            dragPrevCursor = element.style.cursor;
                            element.style.cursor = dragCursor;
                        }
                    } else if (dragPrevCursor !== undefined) {
                        element.style.cursor = dragPrevCursor;
                        dragPrevCursor = undefined;
                    }
                }
            },
            handleUpEvent: function (event) {
                dragCoordinate = null;
                dragFeature = null;
                return false;
            }
        });

        mapService.addInteraction(dragInteraction);



        var drawInteraction = new ol.interaction.Draw({
            features: features,
            type: 'LineString',
            geometryFunction: geometryFunction,
            maxPoints: 2
        });


        function geometryFunction(coordinates, geometry) {

            var start = coordinates[0];
            var end = coordinates[1];

            if (!geometry) {
                geometry = new ol.geom.Polygon(null);
            }
            boxTopLeft = start;
            boxBottomLeft  =  [start[0], end[1]];
            boxBottomRight = end;
            boxTopRight =  [end[0], start[1]];
            // geometry.setCoordinates([
            //     [start, [start[0], end[1]], end, [end[0], start[1]], start]
            // ]);

            geometry.setCoordinates([
                [boxTopLeft, boxBottomLeft, boxBottomRight , boxTopRight, boxTopLeft]
            ]);

            return geometry;
        }


        drawInteraction.on('drawend', function (event) {
            boundingBox = event.feature.getGeometry().getCoordinates()[0];
            mapService.removeInteraction(drawInteraction);
            // $scope.executeQuery($scope.queryStr);

            var feature = new ol.Feature({
                geometry: new ol.geom.Point(boxTopRight),
                coordinate: event.coordinate,
                name: 'My Point'
              });
              feature.setStyle(rectangularStyle);
              vectorSource.addFeature(feature);
        });
        $scope.dragBox = function() {
            
            mapService.addInteraction(drawInteraction);
            $scope.closeDialog();
        }
    }
})();


/*
    var vectorSource = new ol.source.Vector({
                loader: function(extent, resolution, projection) {
                    var epsg4326Extent =
                        ol.proj.transformExtent(extent, projection, 'EPSG:4326');

                    var param = query.split("{{bbox}}");
                    param = '(' + param[0] +
                        epsg4326Extent[1] + ',' + epsg4326Extent[0] + ',' +
                        epsg4326Extent[3] + ',' + epsg4326Extent[2] + ');' +

                        param[1];

                    $http.post(url, param)
                        .then(function(response) {
                            var features = new ol.format.OSMXML().readFeatures(response.data, {
                                featureProjection: projection
                            });
                            vectorSource.addFeatures(features);
                        });
                },
                strategy: ol.loadingstrategy.bbox
            });
            var vector = new ol.layer.Vector({
                source: vectorSource,
                style: _Style
            });
*/
