appModule.factory('projectService', ['$http', '$rootScope', 'mapService',
    function ($http, $rootScope, mapService) {
    var afterSave;
    return {
        saveProject: function (projectName) {
            
            return mapService.saveMapAs(projectName);
        },
        executeAfterSuccessfulSave: function (layerIdToSavedDataIdMappings) {
            if (afterSave) {
                afterSave();
                afterSave = function () {
                };
            }
            (function () {
                var mapLayers = mapService.getLayers();
                for (var i in mapLayers) {
                    if (!mapLayers[i].getDataSourceName()) {
                        mapLayers[i].setDataSourceName(mapLayers[i].getName());
                    }
                    mapLayers[i].setSavedDataId(layerIdToSavedDataIdMappings[i]);
                }
            }());
        },
        setAfterSave: function (_afterSave) {
            afterSave = _afterSave;
        }
    };
}]);
