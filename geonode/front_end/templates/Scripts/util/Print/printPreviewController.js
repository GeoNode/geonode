appModule.controller('printPreviewController', ['$scope', 'mapService', '$modalInstance', '$rootScope',
    function ($scope, map, $modalInstance, $rootScope) {

        var mapInstance = map.olMap;

        mapInstance.once('postcompose', function (event) {
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
            onShowBackgroundToggle: function () {
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
            onShowBackgroundToggle: function () {
                $scope.footerOptions.height = $scope.footerOptions.showBackground ? 'auto' : 0;
            }
        };

        $scope.highlightTitleBox = function () {
            $(document.querySelector('#map-title-box')).focus();
        };

        $scope.highlightFooterBox = function () {
            $(document.querySelector('#map-footer-box')).focus();
        };

        $scope.downloadMap = function () {
            window.print();
        };

        $scope.close = function () {
            $modalInstance.close();
        }
    }]);
