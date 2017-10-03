mapModule.factory('NullSurfLayer', [
    'layerInterface', 'jantrik.Event',
    function (layerInterface, Event) {
        return function NullLayer() {
            var _thisLayer = this;
            this.events = new Event();

            layerInterface.forEach(function(method) {
                _thisLayer[method] = function() {};
            });

            this.setRenderingMode = function (mode) {
                if (mode) {
                    _thisLayer.tools = mode.tools;
                    _thisLayer.olLayer = mode.olLayer;
                } else {
                    _thisLayer.tools = {};
                }
            };

            this.isWritable = function() {
                return false;
            };

            this.setActive = function() {
            };

            this.isNull = true;
        };
    }
]);