appHelperModule.directive('layerStyleEditor', [
    function () {
        return {
            restrict: 'E',
            scope: {
                layerStyle: '=',
                featureType: '='
            },
            templateUrl: './Templates/layerStyleEditor.html'
        };
    }
]);
