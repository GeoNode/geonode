appHelperModule.directive('visualizationEditor', [
    function () {
        return {
            restrict: 'AE',
            templateUrl: 'static/Templates/visualization.html',
            scope: {
                labelConfig: '=',
                attributeDefs: '=',
                featureType: '=',
                option: '='
            },
            // controller: ['$scope', 'labelingEditorService', function ($scope, labelingEditorService) {
            //     $scope.service = labelingEditorService;
            //     $scope.isPolylineType = $scope.featureType == 'polyline';
            // }
            controller: "visualizationController"
        };
    }
]);
// .factory('', [function () {

//     var factory = {
//         getDefaultLabelConfig: function () {
//             return {
//                 attribute: null,
//                 visibilityZoomLevel: 0,
//                 font: factory.fontFamilies[0].value,
//                 fontStyle: factory.fontStyles[0].value,
//                 fontWeight: factory.fontWeights[0].value,
//                 color: '#000000',
//                 borderColor: '#ffffff',
//                 showBorder: true,
//                 size: 10,
//                 alignment: factory.alignments[0].value,
//                 offsetX: 0,
//                 offsetY: 0,
//                 rotation: 0,
//                 followLine: false,
//                 repeat: false,
//                 repeatInterval: 5,
//                 wrap: false,
//                 wrapPixel: 50
//             };
//         },
//         fontFamilies: [{ label: 'Times', value: 'Times' },
//                     { label: 'Verdana', value: 'Verdana' },
//                     { label: 'Times New Roman', value: 'Times New Roman' },
//                     { label: 'Cambria', value: 'Cambria' },
//                     { label: 'Baskerville', value: 'Baskerville Old Face' },
//                     { label: 'Bodoni', value: 'Bodoni MT' },
//                     { label: 'Serif', value: 'Serif.plain' },
//                     { label: 'Courier New', value: 'Courier New' }],
//         fontWeights: [{ label: 'Normal', value: 'normal' }, { label: 'Bold', value: 'bold' }],
//         fontStyles: [{ label: 'Normal', value: 'normal' }, { label: 'Italic', value: 'italic' }, { label: 'Oblique', value: 'oblique' }],
//         alignments: [{ label: 'Left', value: 1 }, { label: 'Center', value: 0.5 }, { label: 'Right', value: 0 }]
//     };
//     return factory;
// }]);
