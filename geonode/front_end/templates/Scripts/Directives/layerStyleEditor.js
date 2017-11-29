appHelperModule.directive('layerStyleEditor', [
    function () {
        return {
            restrict: 'E',
            scope: {
                layerStyle: '=',
                featureType: '='
            },
            templateUrl: 'static/Templates/layerStyleEditor.html'
        };
    }
]);
