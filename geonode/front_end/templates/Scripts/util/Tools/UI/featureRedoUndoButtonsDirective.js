mapModule.directive('featureRedoUndoButtons', [
    'interactionHandler', 'mapTools',
    function (interactionHandler, mapTools) {
        var _dummyRedoUndoTool = {
            canUndo: function () { return false; },
            canRedo: function () { return false; },
        };

        return {
            restrict: 'EA',
            scope: {
            },
            templateUrl: '/static/Templates/Tools/Layer/featureRedoUndoButtons.html',
            controller: [
                '$scope',
                function ($scope) {
                    var _redoUndoTool = _dummyRedoUndoTool;

                    $scope.enable = {
                        undo: function () {
                            return interactionHandler.isEditing() && _redoUndoTool.canUndo();
                        },
                        redo: function () {
                            return interactionHandler.isEditing() && _redoUndoTool.canRedo();
                        }
                    };

                    $scope.action = {
                        undo: function () {
                            _redoUndoTool.undoLastAction();
                        },
                        redo: function () {
                            _redoUndoTool.redoUndoneAction();
                        }
                    };

                    function setActiveLayer(activeLayer) {
                        _redoUndoTool = activeLayer ? activeLayer.tools.redoUndo : _dummyRedoUndoTool;
                    }

                    mapTools.activeLayer.events.register('changed', setActiveLayer);

                    setActiveLayer(mapTools.activeLayer.getActiveLayer());
                }
            ]
        };
    }
]);