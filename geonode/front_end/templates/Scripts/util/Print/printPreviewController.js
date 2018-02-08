(function() {
    'use strict';

    appModule
        .controller('printPreviewController', printPreviewController);

    printPreviewController.$inject = ['$scope', 'mapService', '$modalInstance', '$rootScope', 'mapTools', '$window', '$http'];

    function printPreviewController($scope, map, $modalInstance, $rootScope, mapTools, $window, $http) {

        var mapInstance = map.olMap;

        mapInstance.once('postcompose', function(event) {
            var canvas = event.context.canvas;
            // $rootScope.mapImage.shapeUrl = canvas.toDataURL('image/png');
        });

        mapInstance.renderSync();

        $scope.legendPositions = ['top', 'right', 'bottom', 'left'];

        $scope.legend = {
            values: map.sortableLayers,
            show: true,
            position: $scope.legendPositions[0]
        };

        $scope.headerOptions = {
            show: true,
            textFieldId: 'map-title-box',
            displayText: map.getMapName() || 'Untitled',
            alignment: 'left',
            fontSize: 20,
            backgroundColor: 'transparent',
            color: '#000000',
            showBackground: true,
            height: 'auto',
            onShowBackgroundToggle: function() {
                $scope.headerOptions.height = $scope.headerOptions.showBackground ? 'auto' : 0;
            }
        };

        $scope.footerOptions = {
            show: true,
            textFieldId: 'map-footer-box',
            displayText: 'Footer',
            alignment: 'left',
            fontSize: 8,
            color: '#000000',
            backgroundColor: 'transparent',
            showBackground: true,
            height: 'auto',
            top: 'sss',
            onShowBackgroundToggle: function() {
                $scope.footerOptions.height = $scope.footerOptions.showBackground ? 'auto' : 0;
            }
        };

        $scope.highlightTitleBox = function() {
            $(document.querySelector('#map-title-box')).focus();
        };

        $scope.highlightFooterBox = function() {
            $(document.querySelector('#map-footer-box')).focus();
        };

        function mapLayers(layers) {
            var baseMap = {
                "baseURL": "https://a.tile.openstreetmap.org/",
                "opacity": 1,
                "type": "OSM",
                "maxExtent": [-20037508.3392, -20037508.3392,
                    20037508.3392,
                    20037508.3392
                ],
                "tileSize": [
                    256,
                    256
                ],
                "extension": "png",
                "resolutions": [
                    156543.03390625,
                    78271.516953125,
                    39135.7584765625,
                    19567.87923828125,
                    9783.939619140625,
                    4891.9698095703125,
                    2445.9849047851562,
                    1222.9924523925781,
                    611.4962261962891,
                    305.74811309814453,
                    152.87405654907226,
                    76.43702827453613,
                    38.218514137268066,
                    19.109257068634033,
                    9.554628534317017,
                    4.777314267158508,
                    2.388657133579254,
                    1.194328566789627,
                    0.5971642833948135
                ]
            };
            var mappedLayers = [];
            for (var k in layers) {
                var layer = layers[k];
                mappedLayers.push({
                    "baseURL": $window.GeoServerTileRoot,
                    "opacity": 1,
                    "singleTile": false,
                    "type": "WMS",
                    "layers": [
                        layer.Name
                    ],
                    "format": "image/png",
                    "styles": [
                        ""
                    ],
                    "customParams": {
                        "TRANSPARENT": true,
                        "TILED": true
                    }
                });
            }

            return mappedLayers;
        }
        $scope.pageSize = 'LEGAL';
        $scope.downloadMap = function() {
            var baseMap = mapTools.baseMap;
            console.log(map);
            // window.print();
            var data = {
                "units": "m",
                "srs": "EPSG:3857",
                "layout": $scope.pageSize,
                "dpi": 75,
                "outputFilename": "GeoExplorer-print",
                "mapTitle": "office point",
                "comment": "This map is about the range and beat under Dhaka division",
                "layers": mapLayers(map.getLayers()),
                "pages": [{
                    "center": [
                        10120869.638616,
                        2744410.2262926
                    ],
                    "scale": 500000,
                    "rotation": 0
                }]
            };

            $http.post('/geoserver/pdf/create.json', data )
                .then(function(res) {
                    console.log(res);

                });
        };

        $scope.closeDialog = function() {
            $modalInstance.close();
        };
    }
})();