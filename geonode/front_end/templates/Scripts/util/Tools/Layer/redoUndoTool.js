mapModule.factory('RedoUndoTool', [
    'RedoUndo',
    function (RedoUndo) {
        return function RedoUndoTool(createFeatureTool, deleteFeatureTool, editFeatureTool) {
            var _redoUno = new RedoUndo();

            createFeatureTool.events.register('created', onCreate);
            deleteFeatureTool.events.register('deleted', onDelete);
            editFeatureTool.events.register('edited', onEdit);

            function flagHasRedoUndo(flags) {
                return flags && (flags.redo || flags.undo);
            }

            function onCreate(surfFeature, flags) {
                if (flagHasRedoUndo(flags)) {
                    return;
                }
                _redoUno.addDone({
                    undo: function () {
                        deleteFeatureTool.deleteFeature(surfFeature, { undo: true });
                    },
                    redo: function () {
                        createFeatureTool.createFeature(surfFeature, { redo: true });
                    }
                });
            }

            function onDelete(surfFeature, flags) {
                if (flagHasRedoUndo(flags)) {
                    return;
                }

                _redoUno.addDone({
                    undo: function () {
                        createFeatureTool.createFeature(surfFeature, { undo: true });
                    },
                    redo: function () {
                        deleteFeatureTool.deleteFeature(surfFeature, { redo: true });
                    }
                });
            }

            function onEdit(newSurfFeature, oldSurfFeature, flags) {
                if (flagHasRedoUndo(flags)) {
                    return;
                }

                _redoUno.addDone({
                    undo: function () {
                        editFeatureTool.editFeature(oldSurfFeature, newSurfFeature, { undo: true });
                    },
                    redo: function () {
                        editFeatureTool.editFeature(newSurfFeature, oldSurfFeature, { redo: true });
                    }
                });
            }

            this.activate = function () {};

            this.deactivate = function () {};

            this.dispose = function (olMap, disposeComponents) {
                if (disposeComponents) {
                    [createFeatureTool, deleteFeatureTool, editFeatureTool].forEach(function(comp) {
                        comp.dispose(olMap);
                    });
                }
            };

            this.canRedo = function () {
                return !editFeatureTool.isEditing && _redoUno.canRedo();
            };

            this.canUndo = function () {
                return !editFeatureTool.isEditing && _redoUno.canUndo();
            };

            this.undoLastAction = _redoUno.undoLastAction;

            this.redoUndoneAction = _redoUno.redoUndoneAction;
        }
    }
]);