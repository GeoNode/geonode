mapModule.factory('SimpleWmsRenderingMode', [
    function() {
        return function SimpleWmsMode(olMap, olLayer, tools) {
            this.tools = tools;
            this.olLayer = olLayer;
            var midLayers = olMap.midLayers.getLayers();
            midLayers.insertAt(midLayers.getLength() - 1, olLayer);

            olLayer.getSource().on('tileloadstart', function () {
                jantrik.EventPool.broadcast('layerLoadingStarted', olLayer);
            });

            olLayer.getSource().on('tileloadend', function () {
                jantrik.EventPool.broadcast('layerLoadingEnded', olLayer);
            });

            olLayer.getSource().on('tileloaderror', function() {
                jantrik.EventPool.broadcast('layerLoadingEnded', olLayer);
            });

            this.dispose = function () {
                for (var t in tools) {
                    var tool = tools[t];
                    tool.deactivate && tool.deactivate();
                    tool.dispose && tool.dispose(olMap);
                }
                midLayers.remove(olLayer);
            };

            this.refresh = function () {
                var params = olLayer.getSource().getParams();
                params.t = new Date().getMilliseconds();
                olLayer.getSource().updateParams(params);
            };
            this.update = function (stylesName) {
                var params = olLayer.getSource().getParams();
                params.STYLES = stylesName;
                params.t = new Date().getMilliseconds();
                olLayer.getSource().updateParams(params);
            };
        }
    }
]);
