mapModule.factory('dataService', ['$http',
    function($http) {

        var factory = {

            getLayerAttributeData: function (layerId, fieldName) {
                //$this.isDataLoading = true;
                $http({
                    method: "GET",
                    url: "/layers/"+layerId+"/unique-value-for-attribute/"+fieldName+"/",
                })
                .success(function (data, status, headers, config) {
                    console.log(data);
                    // data = filterDataIfDateType(data.values);
                    // $scope.originalData = data;
                    // $scope.flags.PropertyData = getUnSelectedItems();
                    // $this.isDataLoading = false;
                })
                .error(function () {
                    //$this.isDataLoading = false;
                });

            }

        };

        return factory;
    }
]);
