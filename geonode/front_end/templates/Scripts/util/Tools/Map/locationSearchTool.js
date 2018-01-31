mapModule.factory('LocationSearchTool', [
    'reprojection', '$q', 'ol', 'google', 'jantrik.Event', 'mapTools', 'surfToastr',
    function (reprojection, $q, ol, google, Event, mapTools, surfToastr) {
        function LocationSearchTool(searchMarker, olMap) {
            var _thisTool = this;
            this.events = new Event();

            var overlay = createOverlay();
            var _geocoder = new google.maps.Geocoder();
            var _currentResult;
            this.search = function (queryString) {
                var deferred = $q.defer();

                function reject() {
                    deferred.reject();
                    _thisTool.clearLocation();
                }

                if (!queryString) {
                    reject();
                } else {
                    _geocoder.geocode({ 'address': queryString }, function (results, status) {
                        if (status == google.maps.GeocoderStatus.OK) {
                            deferred.resolve(results);
                        } else {
                            reject();
                        }
                    });
                }

                return deferred.promise;
            };

            this.showLocation = function (gmapResult) {
                _currentResult = toOLSearchResult(gmapResult);
                searchMarker.setGeometry(new ol.geom.Point(_currentResult.location));
                overlay.setPosition(_currentResult.location);
                olMap.getView().fit(_currentResult.bounds, olMap.getSize());
            };

            this.clearLocation = function () {
                searchMarker.setGeometry(null);
                overlay.setPosition(undefined);
            };

            function createOverlay() {
                var container = document.getElementById('location-search-display-popup');

                if (!container) {
                    return {
                        setPosition: function () { }
                    };
                }

                var latlngContainer = container.querySelector('.latlng');
                var addressContainer = container.querySelector('.address');

                var pointAdder = container.querySelector('.addtolayer');

                var olOverlay = new ol.Overlay(({
                    element: container,
                    offset: [0, -35]
                }));

                olMap.addOverlay(olOverlay);

                pointAdder.onclick = function () {
                    var position = olOverlay.getPosition();
                    var activeLayer = mapTools.activeLayer.getActiveLayer();

                    if (activeLayer && activeLayer.ShapeType == 'point') {
                        var createFeatureTool = activeLayer.tools.createFeature;
                        if (!createFeatureTool.isNull) {
                            createFeatureTool.createGeometry(new ol.geom.Point(position));
                            olOverlay.setPosition(undefined);
                            return;
                        }
                    }

                    surfToastr.info('Please select an editable point layer to add this point');;
                };

                return {
                    setPosition: function (position) {
                        if (position) {
                            latlngContainer.innerHTML = ol.coordinate.format(_currentResult.latLng, "{y}° N, {x}° E", 4);
                            addressContainer.innerHTML = _currentResult.address;
                        }

                        olOverlay.setPosition(position);
                    }
                };
            }

        }

        function toOLSearchResult(gMapResult) {
            var latLng = [gMapResult.geometry.location.lng(), gMapResult.geometry.location.lat()];
            var location = reprojection.coordinate.to3857(latLng);

            var northEast = gMapResult.geometry.viewport.getNorthEast();
            var southWest = gMapResult.geometry.viewport.getSouthWest();

            var bounds = [southWest.lng(), southWest.lat(), northEast.lng(), northEast.lat()];
            bounds = reprojection.extent.to3857(bounds);

            var olResult = {
                address: gMapResult.formatted_address,
                location: location,
                bounds: bounds,
                latLng: latLng
            };

            return olResult;
        }

        return LocationSearchTool;
    }]);
