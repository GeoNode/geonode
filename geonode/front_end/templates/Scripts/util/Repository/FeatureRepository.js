repositoryModule.factory('featureRepository', [
    '$http', 'urlResolver', 'dirtyManager', 'surfToastr',
    function ($http, urlResolver, dirtyManager, surfToastr) {
        
        return {
            saveAttributes: function (layerId, editedAttributes) {
                return $http.post(urlResolver.resolveFeature('SaveAttributes'), {
                    LayerId: layerId,
                    ModifiedAttributes: editedAttributes
                }).success(function() {
                    dirtyManager.setDirty(true);
                });
            },
            removeImage: function (layerId, fid, imageId) {
                return $http.post(urlResolver.resolveFeature("RemoveImage"), { layerId: layerId, fid: fid, imageId: imageId }).success(function () {
                    dirtyManager.setDirty(true);
                    surfToastr.success(appMessages.toastr.fileDeleted());
                }).error(function () {
                    surfToastr.error(appMessages.toastr.deleteImageFailed());
                });
            },
            editFeature: function (params) {
                return $http.post(urlResolver.resolveFeature('SaveFeatureEdited'), params).success(function () {
                    dirtyManager.setDirty(true);
                });
            },
            deleteFeatures: function (deletedFids, layerId) {
                return $http.post(urlResolver.resolveFeature('SaveFeaturesDeleted'), { deletedFids: deletedFids, layerId: layerId }).success(function () {
                    dirtyManager.setDirty(true);
                });
            },
            createFeature: function(params) {
                return $http.post(urlResolver.resolveFeature('SaveCreateNewFeature'), params).success(function () {
                    dirtyManager.setDirty(true);
                });
            }
        };
    }
]);