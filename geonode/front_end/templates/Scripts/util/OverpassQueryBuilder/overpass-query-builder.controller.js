(function() {
    appModule
        .controller('OverpassApiQueryBuilderController', OverpassApiQueryBuilderController);

    OverpassApiQueryBuilderController.$inject = ['$scope', '$modalInstance', 'mapService'];

    function OverpassApiQueryBuilderController($scope, $modalInstance, mapService) {
        this.queryStr = "";
        var styles = {
            'amenity': {
                'parking': [
                    new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: 'rgba(170, 170, 170, 1.0)',
                            width: 1
                        }),
                        fill: new ol.style.Fill({
                            color: 'rgba(170, 170, 170, 0.3)'
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
        /*
           var query = "node[amenity=drinking_water](20.981956742832327,87.86865234374999,26.64745870265938,92.7685546875);out;";
            var osmxmlFormat = new ol.format.OSMXML();

            var vectorSource = new ol.source.Vector({
                loader: function(extent, resolution, projection) {
                    var epsg4326Extent =
                        ol.proj.transformExtent(extent, projection, 'EPSG:4326');
                    var url = 'http://overpass-api.de/api/interpreter';
            // var query = "node[amenity=drinking_water]("+epsg4326Extent.join(',')+");out;";
            
                    $.post(url, {data:query}).then(function(response) {
                        var features = osmxmlFormat.readFeatures(response, { featureProjection: projection });
                        vectorSource.addFeatures(features);
                    });
                },
                strategy: ol.loadingstrategy.tile(ol.tilegrid.createXYZ({
                    maxZoom: 19
                }))
            });
         */
        $scope.executeQuery = function(q) {
            // debugger
            var osmxmlFormat = new ol.format.OSMXML();

            var vectorSource = new ol.source.Vector({
                loader: function(extent, resolution, projection) {
                    var epsg4326Extent =
                        ol.proj.transformExtent(extent, projection, 'EPSG:4326');
                    var url = 'http://overpass-api.de/api/xapi?map?bbox=' +
                        epsg4326Extent.join(',');
                    $.post(url, {data: }).then(function(response) {
                        var features = osmxmlFormat.readFeatures(response, { featureProjection: projection });
                        vectorSource.addFeatures(features);
                    });
                },
                strategy: ol.loadingstrategy.tile(ol.tilegrid.createXYZ({
                    maxZoom: 19
                }))
            });

            var vector = new ol.layer.Vector({
                source: vectorSource,
                style: function(feature, resolution) {
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
            });
            mapService.addVectorLayer(vector);
        };

    }
})();