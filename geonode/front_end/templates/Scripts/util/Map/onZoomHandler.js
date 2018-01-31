appModule.factory('onZoomHandler', ['mapService', '$rootScope', function (mapService, $rootScope) {

    function configureLayerVisibility(layer, mapZoomLevel) {
        var layerVisibilityZoomLevel = layer.getZoomLevel();

        if (layerVisibilityZoomLevel <= mapZoomLevel) {
            if (layer.IsVisible) {
                layer.olLayer.setVisible(true);
            }
            layer.zoomLevelBasedVisibility = true;
        } else {
            layer.olLayer.setVisible(false);
            layer.zoomLevelBasedVisibility = false;
        }
    }

    function configureLabelVisibility(layer, mapZoomLevel) {
        var labelVisibilityZoomLevel = layer.getLabelVisibilityZoomLabel();

        if (labelVisibilityZoomLevel <= mapZoomLevel) {
            setLabledStyle(layer);
        } else {
            setDefaultStyle(layer);
        }
    }

    function setDefaultStyle(layer) {
        layer.olLayer.getSource().updateParams({ env: 'showlabel:false' });
    }

    function setLabledStyle(layer) {
        layer.olLayer.getSource().updateParams({ env: 'showlabel:true' });
    }

    return {
        activate: function (olMap) {
            var currentView = olMap.getView();

            $rootScope.$on('layerPropertiesChanged', function (event, args) {
                var mapZoomLevel = currentView.getZoom();

                configureLayerVisibility(args.layer, mapZoomLevel);
                configureLabelVisibility(args.layer, mapZoomLevel);
            });

            currentView.on('change:resolution', function () {
                var layers = mapService.getLayers();
                var mapZoomLevel = currentView.getZoom();

                for (var i in layers) {
                    var layer = layers[i];
                    configureLayerVisibility(layer, mapZoomLevel);
                    configureLabelVisibility(layer, mapZoomLevel);
                }
            });
        }
    }
}]);

