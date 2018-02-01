mapModule.factory('AttributeDisplayTool', [
    'reprojection', 'jantrik.Event', '$timeout',
    function (reprojection, Event, $timeout) {
        return function AttributeDisplayTool(surfLayer, selectFeatureTool, olOverlay, olMap) {
            var isActivated = false;
            var _thisTool = this;
            var _selectFeatureTool = selectFeatureTool;
            this.events = new Event();

            this.activate = function () {
                if (!isActivated) {
                    selectFeatureTool.activate();
                    _thisTool.hideProperty();
                    isActivated = true;
                }
            };

            this.deactivate = function () {
                if (isActivated) {
                    selectFeatureTool.deactivate();
                    _thisTool.hideProperty();
                    isActivated = false;
                }
            };

            this.dispose = function (disposeComponents) {
                if (disposeComponents) {
                    selectFeatureTool.dispose(disposeComponents);
                }
            };

            function getCenterOfExtent(extent) {
                var x = extent[0] + (extent[2] - extent[0]) / 2;
                var y = extent[3];
                return [x, y];
            }

            this.hideProperty = function () {
                olOverlay.setPosition(undefined);
            };

            function adjustPopupPosition(map, coordinate) {
                var center = map.getView().getCenter();
                //var pixelPosition = map.getPixelFromCoordinate([coordinate[0], coordinate[1]]);
                var pixelPosition = _selectFeatureTool.getCurrentEvent().pixel;
                var mapWidth = $("#map_canvas").width();
                var mapHeight = $("#map_canvas").height();
                var popoverHeight = $(".property-grid-overlay").height();
                var popoverWidth = $(".property-grid-overlay").width();
                var thresholdTop = popoverHeight + 50;
                var thresholdBottom = mapHeight;
                var thresholdLeft = popoverWidth / 2 - 80;
                var thresholdRight = mapWidth - popoverWidth / 2 - 130;
                var newX, newY;
                if (pixelPosition[0] < thresholdLeft || pixelPosition[0] > thresholdRight || pixelPosition[1] < thresholdTop || pixelPosition[1] > thresholdBottom) {
                                    
                    if (pixelPosition[0] < thresholdLeft) {
                        newX = pixelPosition[0] + (thresholdLeft - pixelPosition[0]);
                    } else if (pixelPosition[0] > thresholdRight) {
                        newX = pixelPosition[0] - (pixelPosition[0] - thresholdRight);
                    } else {
                        newX = pixelPosition[0];
                    }
                    if (pixelPosition[1] < thresholdTop) {
                        newY = pixelPosition[1] + (thresholdTop - pixelPosition[1]);
                    } else if (pixelPosition[1] > thresholdBottom) {
                        newY = pixelPosition[1] - (pixelPosition[1] - thresholdBottom);
                    } else {
                        newY = pixelPosition[1];
                    }
                    var newCoordinate = map.getCoordinateFromPixel([newX, newY]);
                    var newCenter = [(center[0] - (newCoordinate[0] - coordinate[0])), (center[1] - (newCoordinate[1] - coordinate[1]))];
                    var pan = ol.animation.pan({
                        duration: 500,
                        source: map.getView().getCenter()
                    });
                    map.beforeRender(pan);
                    map.getView().setCenter(newCenter);
                }
            }

            selectFeatureTool.events.register('selected', function (surfFeature, olFeature) {
                if (!surfLayer.IsVisible) return;

                //var coordinate = getCenterOfExtent(olFeature.getGeometry().getExtent());
                var coordinate = olMap.getCoordinateFromPixel(_selectFeatureTool.getCurrentEvent().pixel);
                olOverlay.setPosition(coordinate);
                
                _thisTool.events.broadcast('selected', surfFeature, olFeature);

                $timeout(function () {
                    adjustPopupPosition(olMap, coordinate);
                });

            }).register('allUnSelected', function () {
                _thisTool.hideProperty();
                _thisTool.events.broadcast('allUnSelected');
            });
        }
    }
]);
