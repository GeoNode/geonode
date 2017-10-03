mapModule.factory('GeoLocationTool', [
    'surfToastr', 'jantrik.Event', 'ol',
    function (surfToastr, Event, ol) {
        function GeoLocationTool(olMarker, accuracyFeature, olView, olGeolocation) {
            var _thisTool = this;

            var _activated = false;

            var _zoomed = false;
            var _minZoomLevel = 12;
            var _autoCenterEnabled = true;

            this.events = new Event();

            olGeolocation.on('change:position', function () {
                if (!_zoomed && olView.getZoom() < _minZoomLevel) {
                    olView.setZoom(_minZoomLevel);
                    _zoomed = true;
                }
                var position = olGeolocation.getPosition();
                if (_autoCenterEnabled) {
                    olView.setCenter(position);
                }

                olMarker.setGeometry(new ol.geom.Point(position));
                _thisTool.events.broadcast('updated', position);
            });

            olGeolocation.on('change:accuracyGeometry', function () {
                updateAccuracyCircle();
            });

            olGeolocation.on('locationfailed', function (error) {
                var message = "";
                if (error.code == 1) {
                    message = appMessages.toastr.locationServiceDisabled();
                }
                surfToastr.error(message, appMessages.toastr.unableToStartGpsTitle());
                _zoomed = false;
                _thisTool.deactivate();
                _thisTool.events.broadcast('failed');
            });

            olGeolocation.on('locationuncapable', function () {
                _zoomed = false;
                _thisTool.deactivate();
                _thisTool.events.broadcast('uncapable');
            });

            this.setAutoCenterEnabled = function (enabled) {
                _autoCenterEnabled = enabled;
            };

            this.isAutoCenterEnabled = function () {
                return _autoCenterEnabled;
            };

            this.activate = function () {
                olGeolocation.setTracking(true);
                _activated = true;
                _thisTool.events.broadcast('activated');
            };

            this.deactivate = function () {
                olGeolocation.setTracking(false);
                olMarker.setGeometry(null);
                accuracyFeature.setGeometry(null);
                _zoomed = false;
                _activated = false;
                _thisTool.events.broadcast('deactivated');
            };

            this.isActive = function () {
                return _activated;
            };

            this.getCurrentLocation = function () {
                return olGeolocation.getPosition();
            };

            function updateAccuracyCircle() {
                accuracyFeature.setGeometry(olGeolocation.getAccuracyGeometry());
            }
        }

        return GeoLocationTool;
    }
]);

function fakeGPS(radiusInDegrees) {
    radiusInDegrees = radiusInDegrees || .5;
    var diaInDegrees = radiusInDegrees * 2;
    // crossman: -77.14 38.9020
    // dhaka: 90.3667 23.7
    var location = {
        timestamp: 0,
        coords: {
            longitude: -77.14,
            latitude: 38.9020,
            accuracy: 1000
        }
    };
    
    navigator.geolocation.getCurrentPosition = function (callback) {
        location = angular.copy(location);
        updateLocation(location);
        callback(location);
    };

    navigator.geolocation.watchPosition = function (callback) {
        return setInterval(function () {
            if (Math.random() < .5) {
                navigator.geolocation.getCurrentPosition(callback);
            }
        }, 1000);
    };

    navigator.geolocation.clearWatch = function (watchId) {
        clearInterval(watchId);
    };

    function updateLocation(loc) {
        loc.timestamp++;
        loc.coords.latitude += ((Math.random() * diaInDegrees) - radiusInDegrees);
        loc.coords.longitude += ((Math.random() * diaInDegrees) - radiusInDegrees);
        if (Math.random() < .25) {
            loc.coords.accuracy = 1000 + (2000 * (Math.random() - .5));
        }
    }
}

// fakeGPS(.01);