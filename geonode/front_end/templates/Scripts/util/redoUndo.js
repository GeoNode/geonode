appModule.factory('RedoUndo', [
    function () {
        function RedoUndo() {
            var _this = this;
            var undoneActions = [];
            var doneActions = [];

            this.addDone = function (undoRedoActions) {
                doneActions.push(undoRedoActions);
                undoneActions.length = 0;
            };

            this.undoLastAction = function () {
                if (_this.canUndo()) {
                    var action = doneActions.pop();
                    action.undo();
                    undoneActions.push(action);
                    return true;
                }
                return false;
            };

            this.redoUndoneAction = function () {
                if (_this.canRedo()) {
                    var action = undoneActions.pop();
                    action.redo();
                    doneActions.push(action);
                    return true;
                }
                return false;
            };

            this.canRedo = function () {
                return undoneActions.length > 0;
            };

            this.canUndo = function () {
                return doneActions.length > 0;
            };

            this.resetActions = function () {
                undoneActions = [];
                doneActions = [];
            };
        }

        return RedoUndo;
    }
]);