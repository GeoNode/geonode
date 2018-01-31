mapModule.factory('NavigationHistoryTool', [
    'RedoUndo', '$timeout',
    function NavigationHistoryTool(RedoUndo, $timeout) {
        return function (olMap) {
            var _redoUndo = new RedoUndo();

            var undoingRedoing = true;

            var _lastZoom, _lastCenter;
            

            function panTo(zoom, center) {
                if (zoom && center) {
                    undoingRedoing = true;
                    olMap.getView().setZoom(zoom);
                    olMap.getView().setCenter(center);
                }
            }

            function onMapMove(event) {
                var zoom = event.map.getView().getZoom();
                var center = event.map.getView().getCenter();

                var __zoom = _lastZoom;
                var __center = _lastCenter;

                _lastZoom = zoom;
                _lastCenter = center;

                if (undoingRedoing) {
                    undoingRedoing = false;
                    return;
                }

                _redoUndo.addDone({
                    undo: function () {
                        panTo(__zoom, __center);
                    },
                    redo: function () {
                        panTo(zoom, center);
                    }
                });
            }

            olMap.on('moveend', function(event) {
                $timeout(function() {
                    onMapMove(event);
                });
            });

            this.canForward = _redoUndo.canRedo;
            this.canBack = _redoUndo.canUndo;
            this.forward = _redoUndo.redoUndoneAction;
            this.back = _redoUndo.undoLastAction;
        }
    }
]);