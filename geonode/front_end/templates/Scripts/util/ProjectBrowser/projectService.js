(function() {
    'use strict';

    appModule
        .factory('projectService', projectService);
    projectService.$inject = ['$http', '$rootScope', 'mapService', 'userProfileService'];

    function projectService($http, $rootScope, mapService, userProfileService) {
        var afterSave;
        return {
            getUserProfile: function() {
                return userProfileService.getUserProfile();
            },
            getUserOrganizationList: function(userId) {
                return userProfileService.getUserOrganizationList(userId);
            },
            getCategoryList: function() {
                return mapService.getCategoryList();
            },

            saveProject: function(projectName,abstract,organizationId,categoryId) {

                return mapService.saveMapAs(projectName,abstract,organizationId,categoryId);
            },
            executeAfterSuccessfulSave: function(layerIdToSavedDataIdMappings) {
                if (afterSave) {
                    afterSave();
                    afterSave = function() {};
                }
                (function() {
                    var mapLayers = mapService.getLayers();
                    for (var i in mapLayers) {
                        if (!mapLayers[i].getDataSourceName()) {
                            mapLayers[i].setDataSourceName(mapLayers[i].getName());
                        }
                        mapLayers[i].setSavedDataId(layerIdToSavedDataIdMappings[i]);
                    }
                }());
            },
            setAfterSave: function(_afterSave) {
                afterSave = _afterSave;
            }
        };
    };


})();