mapModule.directive('locationCaptureButtons', [
    'interactionHandler', 'mapTools',
    function (interactionHandler, mapTools) {
        var _dummyLocationCaptureTool = {
            startRecording: function () { },
            pauseRecording: function () { },
            stopRecording: function () { },
            capture: function () { },
        };
        return {
            restrict: 'EA',
            scope: {
            },
            templateUrl: '/static/Templates/Tools/Layer/locationCaptureButtons.html',
            controller: [
                '$scope',
                function ($scope) {
                    var _geoLocationTool = mapTools.geoLocation;
                    var _activeLayerTool = mapTools.activeLayer;
                    var _isPointLayer = false;
                    $scope.show = _geoLocationTool.isActive();

                    var _locationCaptureTool = _dummyLocationCaptureTool;

                    $scope.settings = {
                        recordingInterval: 1,
                        isRecodring: false
                    };

                    $scope.recordingIntervalChanged = function () {
                        if ($scope.settings.isRecodring) {
                            _locationCaptureTool.startRecording($scope.settings.recordingInterval * 1000);
                        }
                    };

                    $scope.startRecording = function () {
                        _locationCaptureTool.startRecording($scope.settings.recordingInterval * 1000);
                        $scope.settings.isRecording = true;
                    };

                    $scope.pauseRecording = function () {
                        _locationCaptureTool.pauseRecording();
                        $scope.settings.isRecording = false;
                    };

                    $scope.stopRecording = function () {
                        _locationCaptureTool.stopRecording();
                        $scope.settings.isRecording = false;
                    };

                    $scope.capture = function () {
                        _locationCaptureTool.capture();
                    };

                    $scope.showPauseRecording = function() {
                        return $scope.settings.isRecording && !_isPointLayer;
                    };

                    function setActiveLayer(activeLayer) {
                        if ($scope.settings.isRecording) {
                            $scope.stopRecording();
                        }
                        if (activeLayer) {
                            _locationCaptureTool = activeLayer.tools.locationCapture;
                            _isPointLayer = activeLayer.ShapeType == 'point';
                        } else {
                            _locationCaptureTool = _dummyLocationCaptureTool;
                            _isPointLayer = false;
                        }
                    }
                    
                    _activeLayerTool.events.register('changed', setActiveLayer);
                    setActiveLayer(_activeLayerTool.getActiveLayer());

                    _geoLocationTool.events.register('activated', function() {
                        $scope.show = true;

                        // TODO: remove this dependency on interaction handler
                        interactionHandler.setTracking(true);
                    }).register('deactivated', function() {
                        $scope.show = false;

                        // TODO: remove this dependency on interaction handler
                        interactionHandler.setTracking(true);
                    });
                }
            ]
        };
    }
]);