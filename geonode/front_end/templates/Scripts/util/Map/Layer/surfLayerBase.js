mapModule
.value('layerInterface', ['setMap', 'unsetMap', 'applyStyle', 'getDataId', 'setLayerVisible', 'setCreateFeatureEnabled', 'setEditFeatureEnabled', 'setRenderingMode', 'setAttributeDefinition', 'setSavedDataId'])
.factory('SurfLayerBase', [
    'layerInterface', 'jantrik.Event',
    function (layerInterface, Event) {
        return function LayerBase(layerInfo) {
            var _thisLayer = this;
            var _active;
            var _mode;

            layerInterface.forEach(function (method) {
                _thisLayer[method] = function () { };
            });

            var _style = { tiled: true };

            this.events = new Event();

            this.setActive = function (active) {
                _active = active;
            };

            this.isActive = function () {
                return _active;
            };

            this.linearUnit = layerInfo.LinearUnit;

            this.zoom = function () { };

            this.getViewableTextLength = function () {
                var initialLength = 25;
                if (!layerInfo.CanWrite) {
                    initialLength -= 4;
                }
                if (!layerInfo.SourceFileExists) {
                    initialLength -= 3;
                }
                return initialLength;
            };

            this.isSourceFileExists = function () {
                return layerInfo.SourceFileExists | true; // |true will only added for debugging purpose
            };

            this.setSortOrder = function (sortOrder) {
                layerInfo.SortOrder = sortOrder;
            };

            this.getStyleName = function () {
                return this.getStyle().Name;
            };
            
            this.getLabeledStyleName = function () {
                return this.getStyle().Name;
            };

            this.getSelectStyleName = function() {
                return this.getStyle().Name;
            };

            this.getSortOrder = function () {
                return layerInfo.SortOrder;
            };

            this.getFeatureType = function () {
                return layerInfo.ShapeType;
            };
            this.getDefaultStyle = function () {
                return _style['default'];
            };

            this.getStyle = function () {
                return _style;
            };

            this.getSelectedOlStyle = function () {
                var ol3Style = new ol.format.Style();
                return ol3Style.getStyle(_style['select']);
            };

            this.setStyle = function (style) {
                if (style) {
                    _style = { };
                    angular.extend(_style, style);
                }
            };

            this.applyStyle = function () { };

            var _removed = false;
            this.markRemoved = function () {
                _removed = true;
            };

            this.isRemoved = function () {
                return _removed;
            };

            this.getId = function () {
                return layerInfo.LayerId;
            };

            this.getName = function () {
                return layerInfo.Name;
            };

            this.getZoomLevel = function () {
                return layerInfo.ZoomLevel;
            }

            this.getLabelVisibilityZoomLabel = function () {
                if (_style.labelConfig) {
                    return _style.labelConfig.visibilityZoomLevel;
                } else {
                    return _style.LabelConfig.VisibilityZoomLevel;
                }
            }

            this.getDataSourceName = function () {
                return layerInfo.DataSourceName;
            };

            this.setDataSourceName = function (dataSourceName) {
                layerInfo.DataSourceName = dataSourceName;
            };

            this.isWritable = function () {
                return layerInfo.CanWrite;
            };

            this.getClassifierDefinitions = function () {
                return this.getStyle().classifierDefinitions;
            };

            this.hasClassifierDefinitions = function () {
                return layerInfo.ClassifierDefinitions && layerInfo.ClassifierDefinitions.selectedField;
            };

            this.hasLabeling = function () {
                return _style.labelConfig && _style.labelConfig.attribute;
            }

            this.setName = function (name) {
                layerInfo.Name = name;
            };

            this.setTiled = function(isTiled){
                _style.tiled = isTiled;
            };

            this.setZoomLevel = function (zoomLevel) {
                layerInfo.ZoomLevel = zoomLevel;
            };

            this.refresh = function () {
                _mode.update(this.getStyleName(), _style.tiled);
                _thisLayer.events.broadcast('refreshed');
            };

            this.setRenderingMode = function (mode) {
                _mode && _mode.dispose();
                _mode = mode;
                if (_mode) {
                    _thisLayer.tools = _mode.tools;
                    _thisLayer.olLayer = _mode.olLayer;
                } else {
                    _thisLayer.tools = {};
                }
            };

            (function () {
                try {
                    layerInfo.AttributeValues = layerInfo.AttributeValues || [];
                } catch (e) {
                }
                _thisLayer.setName(layerInfo.Name);
                _thisLayer.setStyle(layerInfo.Style);
                _thisLayer._features = {};

                angular.extend(_thisLayer, layerInfo);
            })();
        }
    }
])