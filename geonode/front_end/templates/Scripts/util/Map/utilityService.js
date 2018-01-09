mapModule.factory('utilityService', ['$http',
    function($http) {

        var factory = {

            getChartSelectedAttributes: function (chartConfig) {
                var selectedAttributes = _.filter(chartConfig.chartAttributeList, function (attribute) { 
                    return attribute.checked == true;
                });
                return selectedAttributes;
            }
        };

        return factory;
    }
]);
