appModule.controller('catalogBrowserController', catalogBrowserController);
catalogBrowserController.$inject = ['$scope',
    '$rootScope',
    '$modal',
    'catalogDataService',
    'surfToastr',
    'subscriptionStatus',
    'mapService',
    '$timeout',
    'urlResolver',
    '$window',
    'helperService',
    '$http',
    'catalogRepository',
    'layerRepository',
    'layerService',
    '$modalInstance'
];

function catalogBrowserController($scope, $rootScope, $modal, catalogDataService, surfToastr, subscriptionStatus, mapService, $timeout, urlResolver, $window, helperService, $http, catalogRepository, layerRepository, layerService, $modalInstance) {
    $scope.addOnProgress = false;
    $scope.copyOnProgress = false;
    $scope.deleteOnProgress = false;
    $scope.currentlyViewingFiles = [];
    $scope.selectedFolderName = "";
    $scope.selectedFile = {};
    $scope.file = { saveAs: "" };
    $scope.data = { loading: true };
    $scope.searchFilter = { queryText: "" };
    $scope.type = { isCatalog: true };

    $scope.templates = {
        viewSelection: '/static/Templates/CatalogBrowser/viewSelection.html',
        listView: '/static/Templates/CatalogBrowser/listView.html',
        gridView: '/static/Templates/CatalogBrowser/gridView.html',
        properties: '/static/Templates/CatalogBrowser/properties.html'
    };

    $scope.serverList = [{
            name: 'Geoserver',
            method: loadLayersByApi
        },
        // {
        //     name: 'geodata.nationaalgeoregister',
        //     url: 'https://geodata.nationaalgeoregister.nl/bestuurlijkegrenzen/wms',
        //     type: 'wms',
        //     method: loadLayersByWms

        // }
    ];

    function loadLayersByWms(server) {
        var url = server.url + '?service=wms&tiled=true&request=GetCapabilities&access_token=9df608bcabe911e7a833080027252357';
        layerService.fetchWmsLayers(url)
            .then(function(res) {
                $scope.layers = res;
                $scope.layers.forEach(function(e) {
                    e.geoserverUrl = server.url;
                }, this);
            });
    }

    function loadLayersByApi(server) {
        layerService.fetchLayers()
            .then(function(res) {
                $scope.layers = res;
            });
    }
    $scope.loadLayers = function(server) {
        $scope.selectedServerName = server.name;
        server.method(server);

    };

    $scope.addLayer = function(layer) {
        console.log(layer);
        $rootScope.$broadcast('LayerAdded', layer);
    }

    var editingFileName;

    $scope.addToProject = function() {
        $scope.addOnProgress = true;
        if ($scope.selectedFile.DataType == 'csv') {
            $rootScope.editCSV();
            $scope.addOnProgress = false;
            return;
        }
        var selectedData = $scope.selectedFile;
        if (!$scope.usedDataIds[selectedData.DataId]) {
            mapService.addDataLayer(selectedData.DataId, selectedData.DataType, selectedData.ShapeType);
            $scope.usedDataIds[selectedData.DataId] = true;
        } else {
            surfToastr.error(appMessages.toastr.dataInUse());
        }
        $timeout(function() {
            $scope.addOnProgress = false;
        });
    }

    $rootScope.editCSV = function() {
        $modal.open({
            templateUrl: '/static/Templates/CSVEditor.html',
            controller: 'CSVEditorController',
            backdrop: 'static',
            keyboard: false,
            windowClass: 'csv-editor-modal',
            resolve: {
                dataId: function() {
                    return $scope.selectedFile.DataId;
                },
                isReadOnly: function() {
                    return $scope.selectedFolderName == 'Shared with me';
                }
            }
        });
    };

    $scope.upload = function() {
        $modal.open({
            templateUrl: './Catalog/UploadData',
            controller: 'uploadDataController',
            scope: $scope,
            backdrop: 'static',
            keyboard: false
        });
    };

    $scope.rename = function() {
        $scope.editing = true;
        $scope.focus = true;
        editingFileName = $scope.selectedFile.Name;
    };

    $scope.deleteFile = function() {
        $scope.deleteOnProgress = true;
        var selectionId = $scope.selectedFile.DataId;
        var message = getProperWarningMessageForDelete();
        if (selectionId) {
            dialogBox.confirm({
                text: message,
                action: function() {
                    busyStateManager.showBusyState(appMessages.busyState.deleteItem);

                    catalogRepository.deleteData(selectionId).then(function() {
                        surfToastr.success(appMessages.toastr.deleted($scope.selectedFile.Name));
                        subscriptionStatus.decreaseDataStorageUsage($scope.selectedFile.FileSize);
                        $scope.removeSelectedFile();
                        busyStateManager.hideBusyState();
                        $timeout(function() {
                            $scope.deleteOnProgress = false;
                        });
                        setDataSourceNamedOfLayer(selectionId, null, true);
                    });
                },
                width: "350px"
            });
        } else {
            $timeout(function() {
                $scope.deleteOnProgress = false;
            });
        }
    };

    var getProperWarningMessageForDelete = function() {
        if ($scope.selectedFile.IsUsedInProject && $scope.selectedFile.IsShared) {
            return appMessages.confirm.dataSharedAndUsedInMap;
        } else if ($scope.selectedFile.IsUsedInProject) {
            return appMessages.confirm.dataUsedInMap;
        } else if ($scope.selectedFile.IsShared) {
            return appMessages.confirm.dataShared;
        } else {
            return appMessages.confirm.deleteItem;
        }
    };

    $scope.share = function() {
        var selectionId = $scope.selectedFile.DataId;
        if (selectionId) {
            $modal.open({
                templateUrl: './Catalog/Share',
                controller: 'shareDataController',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    selectedDataId: function() {
                        return $scope.selectedFile.DataId;
                    }
                }
            }).result.then(function(isDataShared) {
                $scope.selectedFile.IsShared = isDataShared;
            });
        }
    };

    $scope.closeDialog = function() {
        $modalInstance.close();
    };

    $scope.addFiles = function(files) {
        var l = files.length;
        for (var i = 0; i < l; i++) {
            $scope.addFile(files[i]);
        }
    }

    $scope.addFile = function(file) {
        $scope.folders[0].files.push(file);
        if ($scope.selectedFolderName == $scope.folders[0].name) {
            $scope.currentlyViewingFiles = $scope.folders[0].files;
        }
        $scope.selectedFile = file;
    };

    $scope.cloneSelectedFile = function() {
        $scope.copyOnProgress = true;
        var message = subscriptionStatus.validateTotalStorageLimit($scope.selectedFile.FileSize);
        if (!message) {
            var selection = $scope.selectedFile;
            if (selection.DataId) {
                busyStateManager.showBusyState(appMessages.busyState.createCopy);
                $.post(urlResolver.resolveCatalog("CreateCopy"), { dataId: selection.DataId }, function(file) {
                    $timeout(function() {
                        $scope.addFile(file);
                        $scope.copyOnProgress = false;
                    });
                    subscriptionStatus.increaseDataStorageUsage($scope.selectedFile.FileSize);
                    surfToastr.success(appMessages.toastr.copied(selection.Name));
                    busyStateManager.hideBusyState();
                });
            } else {
                $timeout(function() {
                    $scope.copyOnProgress = false;
                });
            }
        } else {
            subscriptionStatus.showValidationFailMessage(message);
            $scope.copyOnProgress = false;
        }
    };

    $scope.downloadSelectedFile = function() {
        var selection = $scope.selectedFile;
        if (selection.DataId) {
            $window.open("/Catalog/DownloadDataFile?dataId=" + selection.DataId);
        }
    };

    $scope.removeSelectedFile = function() {
        $timeout(function() {
            $scope.currentlyViewingFiles.splice($scope.currentlyViewingFiles.indexOf($scope.selectedFile), 1);
            $scope.selectedFile = {};
        });
    };

    $scope.setData = function(folders) {
        $scope.folders = folders;
        folders[0] && $scope.selectFolder(folders[0]);
    };

    $scope.fetchData = function() {
        catalogDataService.getUsedDataIds().success(function(usedDataIds) {
            $scope.usedDataIds = {};
            for (var i in usedDataIds) {
                $scope.usedDataIds[usedDataIds[i]] = true;
            }

            $http({ url: urlResolver.resolveCatalog("CatalogData"), method: 'GET' })
                .success(function(data) {
                    catalogDataService.setData(data);
                    $scope.data.loading = false;
                    $scope.setData(data);
                }).error(function() {
                    $scope.data.loading = false;
                });
        });
    };

    $scope.selectFolder = function(folder) {
        $scope.selectedFolderName = folder.name;
        $scope.currentlyViewingFiles = folder.files;
        $scope.selectedFile = {};
    };

    $scope.selectData = function(dataInfo) {
        if (dataInfo.IsLocked) {
            surfToastr.error(appMessages.toastr.dataLocked(), appMessages.toastr.upgradeRequiredTitle());
            return;
        }
        $scope.selectedFile = dataInfo;
        $scope.file.saveAs = dataInfo.Name;
    };

    $scope.enableAddToProject = function() {
        if (!$scope.selectedFile.Name || $scope.addOnProgress || $scope.deleteOnProgress) {
            return false;
        }
        return !$scope.usedDataIds[$scope.selectedFile.DataId];
    };

    $scope.enableCopy = function() {
        return $scope.selectedFile.Name && $scope.selectedFile.DataType !== "raster" && !$scope.deleteOnProgress && !$scope.copyOnProgress;
    };

    $scope.enableDelete = function() {
        return $scope.selectedFile.Name && !$scope.copyOnProgress && !$scope.addOnProgress;
    };

    $scope.isSharedFilesShown = function() {
        return $scope.selectedFolderName == "Shared with me";
    }

    function setDataSourceNamedOfLayer(fileDataId, fileName, makeLayerDirty) {
        var layers = mapService.getLayers();
        for (var i in layers) {
            if (layers[i].getSavedDataId() == fileDataId) {
                layers[i].setDataSourceName(fileName);
                if (makeLayerDirty) {
                    layerRepository.makeLayerEdited(layers[i].getId());
                }
                return;
            }
        }
    }

    var finishEditing = function(file) {
        $scope.editing = false;
        if (editingFileName == file.Name) {
            return;
        }
        var failed = helperService.rename($scope, file, urlResolver.resolveCatalog("Rename"));
        if (failed) {
            file.Name = editingFileName;
            $scope.editing = true;
        } else {
            setDataSourceNamedOfLayer(file.DataId, file.Name);
        }
    };

    $scope.stopEditing = function(file) {
        if (!$scope.editing) return;
        if (!$scope.enter) {
            finishEditing(file);
        }
        $scope.editing = false;
        $scope.enter = false;
    };

    $scope.saveIfEnterPressed = function(event, file) {
        if (event.keyCode == 13) {
            $scope.enter = true;
            finishEditing(file);
        }
    };

    $scope.action = {
        doubleClick: function() {
            $scope.addToProject();
        },
        click: function(data) {
            $scope.selectData(data);
        }
    };
}