(function() {
    appModule
        .controller('OverpassApiQueryBuilderController', OverpassApiQueryBuilderController);

    OverpassApiQueryBuilderController.$inject = ['$scope', 'mapService', '$http', '$compile', 'BoxDrawTool', 'layerService', '$window', '$modal', 'surfToastr'];

    function OverpassApiQueryBuilderController($scope, mapService, $http, $compile, BoxDrawTool, layerService, $window, $modal, surfToastr) {
        mapService.removeUserInteractions();
        mapService.removeEvents();
        var boxTool = new BoxDrawTool();
        var url = 'http://overpass-api.de/api/interpreter';
        // $scope.queryStr = "node({{bbox}});out;";
        $scope.queryStr = "";
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

        $scope.closeDialog = function() {
            // $modalInstance.close();
            if (vectorLayer) {
                mapService.removeVectorLayer(vectorLayer);
            }
            boxTool.Remove();
            boxTool.Stop();
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

                            radius: 10,
                        })
                    })
                ]
            });
            mapService.addVectorLayer(vectorLayer);
        }

        $scope.executeQuery = function(query) {
            if (mapService.getZoom() < 12){
                surfToastr.warning('You need at least 12 zoom level to execute the query', 'Zoom level too high.')
                return ;
            }
            if (vectorLayer) {
                mapService.removeVectorLayer(vectorLayer);
            }
            var extent = mapService.getMapExtent();
            var projection = mapService.getProjection();
            if (boundingBox) {
                extent = ol.extent.boundingExtent([
                    boundingBox[0],
                    boundingBox[2]
                ]);
            }
            var epsg4326Extent =
                ol.proj.transformExtent(extent, projection, 'EPSG:4326');
            var reBbox = /{{bbox}}/g;

            var bbox = epsg4326Extent[1] + ',' +
                epsg4326Extent[0] + ',' +
                epsg4326Extent[3] + ',' +
                epsg4326Extent[2];

            var param = query.replace(reBbox, bbox);

            $http.post(url, param)
                .then(function(response) {
                    var features = new ol.format.OSMXML().readFeatures(response.data, {
                        featureProjection: projection
                    });
                    _AddLayer(features);
                });
        };

        $scope.SaveAsLayer = function() {
            showLayerSaveDialog().result.then(function(res) {
                var features = vectorLayer.getSource().getFeatures();
                layerService.createLayerFromFeature(features, res)
                    .then(function(layer) {
                        surfToastr.success('Layer Created successfully', 'Success');                        
                        if (vectorLayer) {
                            mapService.removeVectorLayer(vectorLayer);
                        }
                        mapService.addDataLayer(layer);
                    }, function() {

                    });
            });
        };

        function showLayerSaveDialog() {
            return $modal.open({
                templateUrl: '/static/layers/_layers-save.html',
                controller: 'LayerSaveController as ctrl',
                backdrop: 'static',
                keyboard: false,
                windowClass: 'fullScreenModal First'
            });
        }

        function onBoxChange(feature, bbox) {
            boundingBox = bbox;
            $scope.executeQuery($scope.queryStr);
        }
        $scope.dragBox = function() {
            boxTool.Draw();
            boxTool.OnBoxDrawEnd(onBoxChange);
            boxTool.OnBoxModificationEnd(onBoxChange);
        };
    }
})();