mapModule.factory('layerRenderingModeFactory', [
    'urlResolver', 'SimpleWmsRenderingMode', 'NullRenderingMode', 'WmsSelectFeatureTool', 'WmsSelectionDisplayTool', 'WmsDeleteFeatureTool', 'RedoUndoTool', 'WmsEditFeatureTool', 'CreateFeatureTool', 'LocationCaptureTool', 'AttributeDisplayTool', 'mapTools', 'jantrik.Event',
    function (urlResolver, SimpleWmsRenderingMode, NullRenderingMode, WmsSelectFeatureTool, WmsSelectionDisplayTool, WmsDeleteFeatureTool, RedoUndoTool, WmsEditFeatureTool, CreateFeatureTool, LocationCaptureTool, AttributeDisplayTool, mapTools, Event) {
        var _olMap, _surfMap;
        var _olInteractiveLayer, _olSelectionDisplayLayer, _propertyGridOverlay;
        var _olGeometryType = new Array();
        _olGeometryType['point'] = 'Point';
        _olGeometryType['polyline'] = 'LineString';
        _olGeometryType['polygon'] = 'Polygon';

        function createNullTool() {
            return {
                isNull: true,
                activate: function () { },
                deactivate: function () { },
                dispose: function () { },
                events: new Event()
            };
        }

        function getNullToolSet() {
            return {
                selectFeature: createNullTool(),
                createFeature: createNullTool(),
                deleteFeature: createNullTool(),
                editFeature: createNullTool(),
                redoUndo: createNullTool(),
                locationCapture: createNullTool(),
                clearFeatures: createNullTool(),
                displayAttribute: createNullTool()
            };
        }

        function createWmsSelectFeatureTool(surfLayer, olLayer) {
            var wmsSelectFeatureTool = new WmsSelectFeatureTool(_olMap, surfLayer, olLayer, _surfMap);
            return wmsSelectFeatureTool;
        }

        var selectionDisplayTool;
        function createWmsSelectionDisplayTool(surfLayer, olLayer) {
            var wmsSelectFeatureTool = createWmsSelectFeatureTool(surfLayer, olLayer);
            selectionDisplayTool = new WmsSelectionDisplayTool(surfLayer, wmsSelectFeatureTool, _olSelectionDisplayLayer);
            return selectionDisplayTool;
        }

        function createWmsDeleteFeatureTool(surfLayer, olLayer) {
            var wmsSelectFeatureTool = createWmsSelectFeatureTool(surfLayer, olLayer);
            var wmsDeleteFeatureTool = new WmsDeleteFeatureTool(surfLayer, wmsSelectFeatureTool);

            return wmsDeleteFeatureTool;
        }

        function createRedoUndoTool(createFeatureTool, deleteFeatureTool, editFeatureTool) {
            var redoUndoTool = new RedoUndoTool(createFeatureTool, deleteFeatureTool, editFeatureTool);
            return redoUndoTool;
        }

        // function createClearFeaturesTool(surfLayer) {
        //     return new ClearFeaturesTool(surfLayer);
        // }

        function createWmsEditFeatureTool(surfLayer, olLayer) {
            var wmsSelectionDisplayTool = createWmsSelectFeatureTool(surfLayer, olLayer);

            var featureCollection = new ol.Collection(_olInteractiveLayer.getSource().getFeatures());
            var modifyInteraction = new ol.interaction.Modify({
                features: featureCollection
            });
            _olMap.addInteraction(modifyInteraction);
            var wmsEditFeatureTool = new WmsEditFeatureTool(surfLayer, wmsSelectionDisplayTool, modifyInteraction, _olInteractiveLayer.getSource(), featureCollection);
            return wmsEditFeatureTool;
        }

        function createCreateFeatureTool(surfLayer) {
            var drawInteraction = new ol.interaction.Draw({
                source: _olInteractiveLayer.getSource(),
                type: _olGeometryType[surfLayer.ShapeType]
            });
            _olMap.addInteraction(drawInteraction);
            var createFeatureTool = new CreateFeatureTool(surfLayer, drawInteraction, _olInteractiveLayer.getSource());
            return createFeatureTool;
        }

        function createAttributeDisplayTool(surfLayer, olLayer) {
            if (_surfMap.info && _surfMap.info.PropertyInPopup) {
                var wmsSelectFeatureTool = createWmsSelectFeatureTool(surfLayer, olLayer);
                var attributeDisplayTool = new AttributeDisplayTool(surfLayer, wmsSelectFeatureTool, _propertyGridOverlay, _olMap);
                return attributeDisplayTool;
            }
            return createNullTool();
        }

        function getWmsToolSet(surfLayer, olLayer) {
            var createFeatureTool, wmsDeleteFeatureTool, wmsEditFeatureTool, locationCaptureTool, redoUndoTool;

            if (surfLayer.IsDataOwner) {
                createFeatureTool = createCreateFeatureTool(surfLayer);
                wmsDeleteFeatureTool = createWmsDeleteFeatureTool(surfLayer, olLayer);
                wmsEditFeatureTool = createWmsEditFeatureTool(surfLayer, olLayer);
                locationCaptureTool = createLocationCaptureTool(surfLayer, createFeatureTool);
                redoUndoTool = createRedoUndoTool(createFeatureTool, wmsDeleteFeatureTool, wmsEditFeatureTool);
            } else {
                createFeatureTool = createNullTool();
                wmsDeleteFeatureTool = createNullTool();
                wmsEditFeatureTool = createNullTool();
                locationCaptureTool = createNullTool();
                redoUndoTool = createNullTool();
            }

            return {
                selectFeature: createWmsSelectionDisplayTool(surfLayer, olLayer),
                createFeature: createFeatureTool,
                deleteFeature: wmsDeleteFeatureTool,
                editFeature: wmsEditFeatureTool,
                redoUndo: redoUndoTool,
                locationCapture: locationCaptureTool,
                displayAttribute: createAttributeDisplayTool(surfLayer, olLayer)
            };
        }
        function getWmpVisualizationToolSet(surfLayer, olLayer) {
            var createFeatureTool, wmsDeleteFeatureTool, wmsEditFeatureTool, locationCaptureTool, redoUndoTool;

            if (surfLayer.IsDataOwner && surfLayer.ShapeType !== "geoTiff") {
                createFeatureTool = createCreateFeatureTool(surfLayer);
                wmsDeleteFeatureTool = createWmsDeleteFeatureTool(surfLayer, olLayer);
                wmsEditFeatureTool = createWmsEditFeatureTool(surfLayer, olLayer);
                locationCaptureTool = createLocationCaptureTool(surfLayer, createFeatureTool);
                redoUndoTool = createRedoUndoTool(createFeatureTool, wmsDeleteFeatureTool, wmsEditFeatureTool);
            }
            else {
                createFeatureTool = createNullTool();
                wmsDeleteFeatureTool = createNullTool();
                wmsEditFeatureTool = createNullTool();
                locationCaptureTool = createNullTool();
                redoUndoTool = createNullTool();
            }

            return {
                selectFeature: createWmsSelectionDisplayTool(surfLayer, olLayer),
                createFeature: createFeatureTool,
                deleteFeature: wmsDeleteFeatureTool,
                editFeature: wmsEditFeatureTool,
                redoUndo: redoUndoTool,
                locationCapture: locationCaptureTool,
                displayAttribute: createAttributeDisplayTool(surfLayer, olLayer)
            };
        }
        function createWmsOlLayer(surfLayer) {
            return new ol.layer.Tile({
                source: new ol.source.TileWMS({
                    // url: urlResolver.resolveGeoserverTile(),
                    url: surfLayer.geoserverUrl,
                    params: {
                        // LAYERS: surfLayer.DataId,
                        LAYERS: surfLayer.Name, //new
                        STYLES: surfLayer.Style.Name,
                        FORMAT: 'image/png',
                        TRANSPARENT: true,
                        TILED: surfLayer.tiled
                    }
                }),
                visible: surfLayer.IsVisible
            });
        }

        function craeteVisualizationOlLayer(surfLayer) {
            return new ol.layer.Image({
                source: new ol.source.ImageWMS({
                    url: urlResolver.resolveGeoserverTile(),
                    params: {
                        // LAYERS: surfLayer.DataId,
                        LAYERS: surfLayer.Name, //new
                        STYLES: surfLayer.Style.Name + '_visualization',
                        FORMAT: 'image/png',
                        TRANSPARENT: true
                    }
                }),
                visible: surfLayer.IsVisible
            });
        }

        function createLocationCaptureTool(surfLayer, createFeatureTool) {
            var locationCaptureTool = new LocationCaptureTool(surfLayer, mapTools.geoLocation, createFeatureTool, _olInteractiveLayer.getSource());

            return locationCaptureTool;
        }

        var factory = {
            initialize: function (surfMap, olMap) {
                _olMap = olMap;
                _surfMap = surfMap;

                _olInteractiveLayer = new ol.layer.Vector({
                    source: new ol.source.Vector(),
                    style: ol.interaction.Select.getDefaultStyleFunction()
                });
                //var layers = _surfMap.getLayers();
                //console.log(layers);
                _olSelectionDisplayLayer = new ol.layer.Tile({
                    source: new ol.source.TileWMS({
                        url: urlResolver.resolveGeoserverTile(),
                        params: {
                            LAYERS: '', //layerInfo.DataId,
                            STYLES: '',//layerInfo.Style.Name,
                            FORMAT: 'image/png',
                            TRANSPARENT: true,
                            featureid: 's_aad168c1fbe842a5966d459f07ea1708.404,s_aacc16314499430988b5085ba93e4951.139'
                        }
                    }),
                    visible: true
                });

                _propertyGridOverlay = new ol.Overlay({
                    element: document.getElementById('property-grid-in-overlay')
                });

                _olMap.topLayers.getLayers().push(_olInteractiveLayer);
                _olMap.topLayers.getLayers().push(_olSelectionDisplayLayer);
                _olMap.addOverlay(_propertyGridOverlay);
            },
            createSimpleWmsRenderingMode: function (surfLayer) {
                var olLayer = createWmsOlLayer(surfLayer);
                var tools = getWmsToolSet(surfLayer, olLayer);

                return new SimpleWmsRenderingMode(_olMap, olLayer, tools);
            },
            createVisualizationRenderingMode: function (surfLayer) {
                var olLayer = craeteVisualizationOlLayer(surfLayer);
                var tools = getWmpVisualizationToolSet(surfLayer, olLayer);

                return new SimpleWmsRenderingMode(_olMap, olLayer, tools);
            },
            setNullRenderingMode: function (surfLayer) {
                surfLayer.setRenderingMode(new NullRenderingMode(getNullToolSet()));
            },
            createSimpleRasterRenderingMode: function (surfLayer) {
                var olLayer = createWmsOlLayer(surfLayer);
                var mode = new SimpleWmsRenderingMode(_olMap, olLayer, getNullToolSet());
                return mode;
            },
            setLayerRenderingMode: function (surfLayer) {
                var mode;
                if(surfLayer.style && surfLayer.style.VisualizationSettings){
                    mode = factory.createVisualizationRenderingMode(surfLayer);
                }
                else{
                    if (surfLayer.ShapeType == 'geoTiff' || surfLayer.ShapeType == 'geoPdf'){
                        mode = factory.createSimpleRasterRenderingMode(surfLayer);
                    }
                    else{
                        mode = factory.createSimpleWmsRenderingMode(surfLayer);
                    }
                }
                surfLayer.setRenderingMode(mode);
                if (mapTools.activeLayer) {
                    mapTools.activeLayer.events.broadcast('updateEnableState');
                }
            }
        };
        return factory;
    }
]);
