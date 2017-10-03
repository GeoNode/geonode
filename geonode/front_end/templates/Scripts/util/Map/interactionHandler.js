mapModule.factory('interactionHandler', [
    'mapModes', 'featureService',
    function (mapModes, featureService) {

        var _modeHandler = {};
        _modeHandler[mapModes.addShape] = {
            setMode: function () {
                _surfLayer.tools.createFeature.activate();
                _surfLayer.tools.redoUndo.activate();
            }
        };

        _modeHandler[mapModes.editShape] = {
            setMode: function () {
                _surfLayer.tools.editFeature.activate();
                _surfLayer.tools.redoUndo.activate();
            }
        };

        _modeHandler[mapModes.select] = {
            setMode: function () {
                _surfLayer.tools.selectFeature.activate();
                _surfLayer.tools.displayAttribute.activate();
            }
        };

        _modeHandler[mapModes.deleteShape] = {
            setMode: function () {
                _surfLayer.tools.deleteFeature.activate();
                _surfLayer.tools.redoUndo.activate();
            }
        };

        _modeHandler[mapModes.trackLocation] = {
            setMode: function () {
                _surfLayer.tools.selectFeature.activate();
                _surfLayer.tools.locationCapture.activate();
            }
        };

        var _surfLayer;
        var _mode, _lastEditingMode, _isTracking;

        function setSurfLayer(surfLayer) {
            if (_surfLayer != surfLayer) {
                _surfLayer = surfLayer;
                clearFeatures();

                setMode(mapModes.select);
            }
        }

        function getSurfLayer() {
            return _surfLayer;
        }

        function setMode(mode) {
            deactivateAll();
            _mode = mode;

            if (_surfLayer) {
                _modeHandler[mode].setMode();
            }
        }

        // TODO: REMOVE DUPLICATE -> activeLayerTool
        function deactivateAll() {
            if (_surfLayer && _surfLayer.tools) {
                for (var toolName in _surfLayer.tools) {
                    var tool = _surfLayer.tools[toolName];
                    tool.deactivate && tool.deactivate();
                }
            }
        }

        function clearFeatures() {
            featureService.setActive(null);
        }

        function toggleEditable() {
            if (isEditing()) {
                _lastEditingMode = _mode || mapModes.editShape;
                _surfLayer.tools.editFeature.saveModification();
                _surfLayer.tools.createFeature.saveCreation();
                setMode(mapModes.select);
            } else {
                setMode(_isTracking ? mapModes.trackLocation : _lastEditingMode || mapModes.editShape);
            }
        }

        function isEditing() {
            return _mode && _mode != mapModes.select;
        }

        function getMode() {
            return _mode;
        }

        function setTracking(isTracking) {
            _isTracking = isTracking;
        }

        var factory = {
            setSurfLayer: setSurfLayer,
            getSurfLayer: getSurfLayer,
            deactivateAll: deactivateAll,
            setMode: setMode,
            toggleEditable: toggleEditable,
            isEditing: isEditing,
            getMode: getMode,
            setTracking: setTracking
        }

        return factory;
    }
]);
