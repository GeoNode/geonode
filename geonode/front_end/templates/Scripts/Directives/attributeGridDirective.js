appHelperModule.directive('attributeGrid', ['attributeTypes',
function () {
    return {
        restrict: 'AE',
        scope:{
            layerId: '='
        },
        templateUrl: 'static/Templates/attributeGrid.html',
        controller: 'attributeGridController'
    };
}
]);