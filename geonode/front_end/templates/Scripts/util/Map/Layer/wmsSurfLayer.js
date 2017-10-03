mapModule.factory('WmsSurfLayer', [
    'SurfLayerBase', 'featureFilterGenerator',
    function (SurfLayerBase, featureFilterGenerator) {
        function WmsSurfLayer(layerInfo) {
            SurfLayerBase.call(this, layerInfo);

            function isStyleDisplayVisible(style) {
                return style.display != 'none';
            }

            function setStyleDisplayVisible(style, visible) {
                style.display = visible ? '' : 'none';
            }

            var _thisLayer = this;
            this.inProgress = false;

            var _base = {
                setSortOrder: _thisLayer.setSortOrder,
                setName: _thisLayer.setName,
                setStyle: _thisLayer.setStyle,
                setActive: _thisLayer.setActive,
                setZoomLevel: _thisLayer.setZoomLevel
            };
            var _mapExtent = {};

            this.setMapExtent = function (layerExtent) {
                _mapExtent = [
                    layerExtent.MinX,
                    layerExtent.MinY,
                    layerExtent.MaxX,
                    layerExtent.MaxY
                ];
            }

            this.getMapExtent = function () {
                return _mapExtent;
            }

            this.setMapExtent(layerInfo.LayerExtent);

            var _attributeDefinition = {};

            function updateLayerVisibility() {
                if (!_thisLayer.zoomLevelBasedVisibility && _thisLayer.IsVisible) return;
                _thisLayer.olLayer.setVisible(_thisLayer.IsVisible);
            }

            this.setFilter = function (filter) {
                if (filter) {
                    _thisLayer.olLayer.getSource().updateParams(filter);
                    _thisLayer.events.broadcast('refreshed');
                }
            }

            var _queries = [
                //{ attributeName: 's_303a2536dedc4cc6ab4957f2abd75c6c', type: 'character', value: 2 },
                //{ attributeName: 's_303a2536dedc4cc6ab4957f2abd75c6c', type: 'character', value: 3 }
            ];

            this.setQuery = function (queries) {
                _queries = queries;
            };

            this.getQueries = function () {
                return _queries;
            }

            this.setStyle = function (style) {
                _base.setStyle(style);
                _thisLayer.applyStyle();
                _thisLayer.events.broadcast('styleChanged');
            };

            this.setActive = function (active) {
                _base.setActive(active);
                _thisLayer.updateZIndex();
            };

            this.applyStyle = function () {
            };

            this.setClassifierDefinitions = function (classifierDefinitions) {
                if (!classifierDefinitions || !classifierDefinitions.selectedField) {
                    classifierDefinitions = {};
                }
                layerInfo.ClassifierDefinitions = classifierDefinitions;
            };

            this.loadFeatures = function () {
                _thisLayer.percentLoaded = 100;
                _thisLayer.inProgress = false;
            };

            this.percentLoaded = 100;

            this.getDataId = function () {
                return layerInfo.DataId;
            };

            this.getSavedDataId = function () {
                return layerInfo.SavedDataId;
            }

            this.setSavedDataId = function (savedDataId) {
                layerInfo.SavedDataId = savedDataId;
            }

            var _lastAttributeDefinitionUpdateTime = new Date(0);

            this.setAttributeDefinition = function (attributeDefinition) {
                _attributeDefinition = [];
                for (var i in attributeDefinition) {
                    if (attributeDefinition[i].Status != 'deleted') {
                        _attributeDefinition.push(attributeDefinition[i]);
                    }
                }
                _lastAttributeDefinitionUpdateTime = new Date();
                _thisLayer.setFilter(featureFilterGenerator.getFilter(_thisLayer));
            };

            this.getLastAttributeDefinitionUpdateTime = function () {
                return _lastAttributeDefinitionUpdateTime;
            };

            this.resetLastAttributeDefinitionUpdateTime = function () {
                _lastAttributeDefinitionUpdateTime = new Date();
            };

            this.getAttributeDefinition = function () {
                return _attributeDefinition;
            };

            this.getFeature = function () {
                //return _thisLayer._features[fid];
            };

            this.getAllFeatures = function () {
                //return _thisLayer._features;
            };

            this.addFeature = function () {
            };

            this.updateLayerVisibility = updateLayerVisibility;

            this.updateZIndex = function () {
                var zIndex = _thisLayer.isActive() ? 500 : 500 - _thisLayer.getSortOrder();
                // TODO restore
                //_thisLayer.olLayer.setZIndex(zIndex);
            };

            this.setSortOrder = function (sortOrder) {
                _base.setSortOrder(sortOrder);
                _thisLayer.updateZIndex();
            };

            this.isEmpty = function () {
                return _mapExtent && !_mapExtent[0] && !_mapExtent[1] && !_mapExtent[2] && !_mapExtent[3];
            };

            this.getWrappedLayer = function () {
                return _thisLayer.olLayer;
            };

            this.isClassVisible = function (classObject) {
                return isStyleDisplayVisible(classObject.style);
            };

            this.setClassVisible = function (classObject, visible, preventRedraw) {
                setStyleDisplayVisible(classObject.style, visible);
                classObject.checked = visible;
                if (!preventRedraw) {
                    _thisLayer.refresh();
                }
            };

            this.setName = function (name) {
                _base.setName(name);

                _thisLayer.olLayer.set({
                    name: name
                });
            };

            this.setZoomLevel = function (zoomLevel) {
                _base.setZoomLevel(zoomLevel);

                _thisLayer.olLayer.set({
                    zoomLevel: zoomLevel
                });
            }
        }

        WmsSurfLayer.prototype = Object.create(SurfLayerBase.prototype);
        return WmsSurfLayer;
    }
]);