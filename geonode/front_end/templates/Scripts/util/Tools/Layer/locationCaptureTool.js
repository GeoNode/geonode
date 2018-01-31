mapModule.factory('LocationCaptureTool', [
    'ol', '$interval',
    function (ol, $interval) {
        function PointHandler(createFeatureTool) {
            this.insertPoint = function (olCoordinate) {
                createFeatureTool.createGeometry(new ol.geom.Point(olCoordinate));
            };

            this.complete = function () { };

            this.updateTempPoint = function () { };

            this.isInProgress = function () {
                return true;
            };

            this.reset = function () {
            };
        }

        function PolyHandler(createFeatureTool, interactiveSource) {
            var _thisHandler = this;
            this.currentCoordinates = [];
            var _olCurrentFeature;
            var _olTempFeature;

            this.isInProgress = function () {
                return _thisHandler.currentCoordinates.length > 0;
            };

            this.updateTempPoint = function (/*olCoordinates*/) { /* OVERRIDE */ };

            this.setTempGeom = function (olGeom) {
                _olTempFeature.setGeometry(olGeom);
            };

            this.complete = function () {
                var geometry = _thisHandler.createCurrentGeometry();
                createFeatureTool.createGeometry(geometry);
                _thisHandler.reset();
            };

            this.insertPoint = function (olCoordinate) {
                if (!_olCurrentFeature) {
                    _olCurrentFeature = new ol.Feature();
                    _olTempFeature = new ol.Feature();
                    interactiveSource.addFeature(_olCurrentFeature);
                    interactiveSource.addFeature(_olTempFeature);
                }

                _thisHandler.currentCoordinates.push(olCoordinate);
                _olCurrentFeature.setGeometry(_thisHandler.createCurrentGeometry());
            };

            this.getCurrentGeometry = function () {
                return _olCurrentFeature ? _olCurrentFeature.getGeometry() : null;
            };

            this.reset = function () {
                if (_olCurrentFeature) {
                    interactiveSource.removeFeature(_olCurrentFeature);
                    interactiveSource.removeFeature(_olTempFeature);
                    _olCurrentFeature = null;
                    _olTempFeature = null;
                }

                _thisHandler.currentCoordinates.length = 0;
            };
        }

        function PolylineHandler(createFeatureTool, interactiveSource) {
            PolyHandler.call(this, createFeatureTool, interactiveSource);
            var _thisHandler = this;

            this.updateTempPoint = function (olCoordinates) {
                if (_thisHandler.currentCoordinates.length) {
                    var line = new ol.geom.LineString([_thisHandler.currentCoordinates[_thisHandler.currentCoordinates.length - 1], olCoordinates]);
                    _thisHandler.setTempGeom(line);
                }
            };

            this.createCurrentGeometry = function () {
                return new ol.geom.LineString(_thisHandler.currentCoordinates);
            };

            PolylineHandler.prototype = Object.create(PolyHandler.prototype);
        }

        function PolygonHandler(createFeatureTool, interactiveSource) {
            PolyHandler.call(this, createFeatureTool, interactiveSource);
            var _thisHandler = this;

            this.updateTempPoint = function (olCoordinates) {
                if (_thisHandler.currentCoordinates.length) {
                    var line;
                    if (_thisHandler.currentCoordinates.length == 1) {
                        line = new ol.geom.LineString([
                            _thisHandler.currentCoordinates[0],
                            olCoordinates
                        ]);
                    } else {
                        line = new ol.geom.LineString([
                            _thisHandler.currentCoordinates[0],
                            olCoordinates,
                            _thisHandler.currentCoordinates[_thisHandler.currentCoordinates.length - 1]
                        ]);
                    }

                    _thisHandler.setTempGeom(line);
                }
            };

            this.createCurrentGeometry = function () {
                return new ol.geom.Polygon([_thisHandler.currentCoordinates.concat([_thisHandler.currentCoordinates[0]])]);
            };

            PolygonHandler.prototype = Object.create(PolyHandler.prototype);
        }

        return function LocationCaptureTool(surfLayer, geoLocationTool, createFeatureTool, olInteractiveSource) {
            var _thisTool = this;
            var _activated;
            var _handler;

            if (surfLayer.ShapeType == 'point') {
                _handler = new PointHandler(createFeatureTool);
            } else if (surfLayer.ShapeType == 'polyline') {
                _handler = new PolylineHandler(createFeatureTool, olInteractiveSource);
            } else if (surfLayer.ShapeType == 'polygon') {
                _handler = new PolygonHandler(createFeatureTool, olInteractiveSource);
            }

            function getCurrentLocation() {
                return geoLocationTool.getCurrentLocation();
            }

            var _recordingPromise;

            this.startRecording = function (interval) {
                _thisTool.pauseRecording();

                _thisTool.capture();
                _recordingPromise = $interval(function () {
                    _thisTool.capture();
                }, interval);
            };

            this.pauseRecording = function () {
                if (angular.isDefined(_recordingPromise)) {
                    $interval.cancel(_recordingPromise);
                    _recordingPromise = null;
                }
            };

            this.stopRecording = function () {
                _thisTool.pauseRecording();
                _handler.isInProgress() && _handler.complete();
            };

            this.capture = function () {
                _handler.insertPoint(getCurrentLocation());
            };

            this.isGeometryValid = function () {
                return _handler.isGeometryValid();
            };

            this.activate = function () {
                _activated = true;

                geoLocationTool.events
                    .register('updated', onLocationUpdate)
                    .register('deactivated', onLocationDeactivated);
            };

            this.deactivate = function () {
                geoLocationTool.events
                    .unRegister('updated', onLocationUpdate)
                    .unRegister('deactivated', onLocationDeactivated);

                _thisTool.stopRecording();
                _handler.reset();
                _activated = false;
            };

            function onLocationUpdate() {
                _handler.updateTempPoint(getCurrentLocation());
            }

            function onLocationDeactivated() {
                _thisTool.stopRecording();
            }
        };
    }
]);