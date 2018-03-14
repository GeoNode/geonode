(function () {
    angular
        .module('SystemSettingsApp')
        .controller('SystemSettingsController', SystemSettingsController);

    SystemSettingsController.$inject = ['$scope', 'SettingsService'];

    function SystemSettingsController($scope, SettingsService) {
        $scope.layer=[];
        $scope.addressGeocodeLayer=undefined;
        $scope.elevationRasterLayer=undefined; 
        $scope.vectorLayers=[];
        $scope.rasterLayers=[];

        var systemSettings = SettingsService.getSystemSettings();

        systemSettings.then(function (res) {

                var value=res.results;
                $.each(value, function (index, element) {                    
                    if (element.settings_code == "location") {
                        $scope.addressGeocodeLayer = element.content_object.uuid;
                        checkSelectedLayerAttrhave(element.content_object.uuid);
                    }else if(element.settings_code == "elevation"){
                        $scope.elevationRasterLayer=element.content_object.uuid;
                    }
                });

            }, function (error) {
                // This is called when error occurs.
            }
        );

        var rasterLayerSettings = SettingsService.getLayers("type__in=raster");
        var vectorLayerSettings = SettingsService.getLayers("type__in=vector");

        // var layersObject;

        rasterLayerSettings.then(function (value) {
               var layersObjects = value.objects;
                $.each(layersObjects, function (index, element) {
                    var title = element.title;
                    if (element.title.length > 22) {
                        title = element.title.substring(0, 25) + "...";
                    }
                });
                $scope.rasterLayers=layersObjects;

            }, function (error) {
                // This is called when error occurs.
            }
        );

        vectorLayerSettings.then(function (value) {
                var layersObjects = value.objects;
                $.each(layersObjects, function (index, element) {
                    var title = element.title;
                    if (element.title.length > 22) {
                        title = element.title.substring(0, 25) + "...";
                    }
                });
                $scope.vectorLayers=layersObjects;
            }, function (error) {
                // This is called when error occurs.
            }
         );

        function checkSelectedLayerAttrhave(uuid) {
            var addressColumnsStatus = SettingsService.getAddressAttributes(uuid);
    
            addressColumnsStatus.then(function (value) {
    
                    if (value.status == 'invalid') {
    
                        var columns = value.columns.toString().replaceAll(',', ', ');
    
                        $scope.layerStatusMsg = columns + " are missing!";
    
                    }
    
                }, function (error) {
                    // This is called when error occurs.
                }
            );
        }


        $scope.layerSettingSave = function (settingType,layerUUID) {
            var data = {
                'uuid': layerUUID,
                'settings_code': settingType,
            };
            SettingsService.saveSystemSettings(data);
        };

        $scope.changedValue = function () {
            checkSelectedLayerAttrhave($scope.addressGeocodeLayer);
        };

    }

    
})();
