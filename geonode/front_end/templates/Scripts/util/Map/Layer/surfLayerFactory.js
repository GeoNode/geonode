mapModule.factory('surfLayerFactory', [
    'mapModes', 'SurfFeature', 'mapAccessLevel', 'urlResolver', 'NullSurfLayer', 'SourceLessSurfLayer', 'WmsSurfLayer', 'WmsSelectFeatureTool', 'CreateFeatureTool', 'WmsSelectionDisplayTool', 'WmsDeleteFeatureTool', 'WmsEditFeatureTool', 'RedoUndoTool', 'ClearFeaturesTool', 'SimpleWmsRenderingMode', 'NullRenderingMode', 'layerRenderingModeFactory',
    function (mapModes, SurfFeature, mapAccessLevel, urlResolver, NullSurfLayer, SourceLessSurfLayer, WmsSurfLayer, WmsSelectFeatureTool, CreateFeatureTool, WmsSelectionDisplayTool, WmsDeleteFeatureTool, WmsEditFeatureTool, RedoUndoTool, ClearFeaturesTool, SimpleWmsRenderingMode, NullRenderingMode, layerRenderingModeFactory) {

        return {
            createSurfLayer: function (layerInfo) {
                var surfLayer;
                if (!layerInfo) {
                    surfLayer = new NullSurfLayer();
                    layerRenderingModeFactory.setNullRenderingMode(surfLayer);
                } else {
                    if (!layerInfo.SourceFileExists) {
                        surfLayer = new SourceLessSurfLayer(layerInfo);
                        layerRenderingModeFactory.setNullRenderingMode(surfLayer);
                    } else {
                        surfLayer = new WmsSurfLayer(layerInfo);
                        layerRenderingModeFactory.setLayerRenderingMode(surfLayer);
                    }

                    surfLayer.setAttributeDefinition(layerInfo.AttributeDefinition || []);
                }
                surfLayer.olFeatures = {};
                return surfLayer;
            },
            createSelectionLayer: function () {

                return new ol.layer.Tile({
                    source: new ol.source.TileWMS({
                        url: urlResolver.resolveGeoserverTile(),
                        params: {
                            LAYERS: '',
                            STYLES: '',
                            FORMAT: 'image/png',
                            TRANSPARENT: true,
                            featureid: '?'
                        }
                    }),
                    visible: true
                });
            },
            disposeSurfLayer: function (surfLayer) {
                surfLayer.setRenderingMode(null);
            }
        };
    }
]);
