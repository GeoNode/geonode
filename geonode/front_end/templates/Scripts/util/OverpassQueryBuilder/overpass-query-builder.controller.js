(function() {
    appModule
        .controller('OverpassApiQueryBuilderController', OverpassApiQueryBuilderController);

    OverpassApiQueryBuilderController.$inject = ['$scope', '$modalInstance', 'mapService', '$http', '$compile'];

    function OverpassApiQueryBuilderController($scope, $modalInstance, mapService, $http, $compile) {
        var url = 'http://overpass-api.de/api/interpreter';
        $scope.queryStr = "node({{bbox}});out;";
        var styles = {
            'amenity': {
                '.*': [
                    new ol.style.Style({
                        image: new ol.style.RegularShape({
                            fill: new ol.style.Fill({ color: 'red' }),
                            stroke: new ol.style.Stroke({ color: 'black', width: 2 }),
                            points: 4,
                            radius: 10,
                            radius2: 0,
                            angle: Math.PI / 4
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
        $scope.closeDialog = function() {
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

        function _AddLayer(features) {
            var vectorSource = new ol.source.Vector({
                features: features
            });
            var vector = new ol.layer.Vector({
                source: vectorSource,
                style: _Style
            });
            mapService.addVectorLayer(vector);
        }

        $scope.executeQuery = function(query) {
            var extent = mapService.getMapExtent();
            var projection = mapService.getProjection();
            var epsg4326Extent =
                ol.proj.transformExtent(extent, projection, 'EPSG:4326');

            var param = query.split("{{bbox}}");
            param = '(' + param[0] +
                epsg4326Extent[1] + ',' + epsg4326Extent[0] + ',' +
                epsg4326Extent[3] + ',' + epsg4326Extent[2] +
                ');' + param[1];
            $http.post(url, param)
                .then(function(response) {
                    var features = new ol.format.OSMXML().readFeatures(response.data, {
                        featureProjection: projection
                    });
                    _AddLayer(features);
                });
        };
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
