mapModule.factory('SourceLessSurfLayer', [
    'SurfLayerBase', 'layerInterface', 'ol',
    function (SurfLayerBase, layerInterface, ol) {
        function SourcelessLayer(layerInfo) {
            SurfLayerBase.call(this, layerInfo);

            var _thisLayer = this;
            this.isEmpty = function () {
                return true;
            };

            layerInterface.forEach(function (methodName) {
                _thisLayer[methodName] = _thisLayer[methodName] || function () { };
            });
            
            this.getWrappedLayer = function () {
            };

            this.setActive = function () {
            };

            this.getAttributeDefinition = function () {
                return [];
            };

            this.refresh = function () {
            };

            this.getMapExtent = function() {
                return ol.extent.createEmpty();
            };
        }
        SourcelessLayer.prototype = Object.create(SurfLayerBase.prototype);

        return SourcelessLayer;
    }
]).factory('', [
    'AlwaysSelectableSourcelessSurfLayer',
    function (SourceLessSurfLayer) {
        function AlwaysSelectableSourcelessSurfLayer(layerInfo) {
            SourceLessSurfLayer.call(this, layerInfo);
        };
        
        AlwaysSelectableSourcelessSurfLayer.prototype = Object.create(SourceLessSurfLayer.prototype);

        return AlwaysSelectableSourcelessSurfLayer;
    }
]);


