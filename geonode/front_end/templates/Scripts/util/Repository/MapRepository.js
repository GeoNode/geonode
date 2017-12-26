repositoryModule.factory('mapRepository', [
    '$http', 'urlResolver', 'dirtyManager', 'surfToastr', '$cookies',
    function ($http, urlResolver, dirtyManager, surfToastr, $cookies) {

        return {
            openMap: function (mapId) {
                return $http.post(urlResolver.resolveMap("Open"), { projectId: mapId }).success(function () {
                    dirtyManager.setDirty(false);
                });
            },
            closeMap: function () {
                return $http.get(urlResolver.resolveMap("CloseWorking")).success(function () {
                    dirtyManager.setDirty(false);
                });
            },
            updateSortOrder: function (sortOrderMappings) {
                return $http.post(urlResolver.resolveMap('UpdateSortOrder'), sortOrderMappings).success(function () {
                    dirtyManager.setDirty(true);
                });
            },
            getMapInfo: function (publicId) {
                return $http.get(urlResolver.resolveMap('GetPublicMapInfo', { publicId: publicId }));
            },
            getWorkingMapInfo: function () {
                return $http.post(urlResolver.resolveMap('GetWorkingProject')).success(function(mapInfo) {
                    dirtyManager.setDirty(mapInfo.IsDirty);
                });
            },
            saveBaseLayerName: function (baseLayerName) {
                return $http.post(urlResolver.resolveMap('SaveBaseLayerName'), { baseLayerName: baseLayerName }).success(function () {
                    dirtyManager.setDirty(true);
                });
            },
            createBlankLayer: function (data) {
                return $http.post(urlResolver.resolveLayer("CreateBlankLayer"), data).success(function () {
                    dirtyManager.setDirty(true);
                    surfToastr.success(appMessages.toastr.blankLayerAdded());
                });
            },
            createDataLayer: function (data) {
                return $http.post(urlResolver.resolveLayer("AddLayerFromData"), data).success(function (layerInfo) {
                    dirtyManager.setDirty(true);
                    surfToastr.success(appMessages.toastr.layerAdded(layerInfo.Name));
                });
            },
            createRasterDataLayer: function (data) {
                return $http.post(urlResolver.resolveLayer("AddRasterLayerFromData"), data).success(function (layerInfo) {
                    dirtyManager.setDirty(true);
                    surfToastr.success(appMessages.toastr.layerAdded(layerInfo.Name));
                });
            },
            removeLayer: function (layerId) {
                return $http.post(urlResolver.resolveLayer("RemoveLayer"), { layerId: layerId }).success(function () {
                    dirtyManager.setDirty(true);
                });
            },
            // saveAs: function (name) { // old
            //     return $http.get(urlResolver.resolveMap("SaveAs", { projectName: name })).success(function () {
            //         dirtyManager.setDirty(false);
            //         surfToastr.success(appMessages.toastr.mapSaveAs(name));
            //     });
            // },
            saveAs: function (obj) { //new
                return $http.post('maps/new/data', obj, {
                    headers: {
                        "X-CSRFToken": $cookies.get('csrftoken')
                    }
                }).success(function () {
                    dirtyManager.setDirty(false);
                    surfToastr.success(appMessages.toastr.mapSaveAs(name));
                });
            },
            getMapSummary: function (mapId) {
                return  $http.get(urlResolver.resolveMap('GetMapSummary', { mapId: mapId }));
            },
            saveMapSummary: function(mapSummary) {
                return $http.post(urlResolver.resolveMap('SaveMapSummary'), mapSummary);
            }
        };
    }
]);