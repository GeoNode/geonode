appModule.controller('projectBrowserController', ['$scope', '$window', '$rootScope', 'showProjectNameInput', 'projectService', '$modalInstance', 'surfToastr', '$modal', 'mapService', 'dirtyManager', 'urlResolver', 'subscriptionStatus', 'helperService', '$http',
    function($scope, $window, $rootScope, showProjectNameInput, projectService, $modalInstance, surfToastr, $modal, mapService, dirtyManager, urlResolver, subscriptionStatus, helperService, $http) {
        $scope.project = { showNameInput: showProjectNameInput };
        $scope.currentlyViewingFiles = [];
        $scope.selectedFolderName = "";
        $scope.selectedFile = {};
        $scope.file = { saveAs: mapService.getMapName() };
        $scope.data = { loading: true };
        $scope.searchFilter = { queryText: "" };
        $scope.type = { isProject: true };

        $scope.UserOrganizationList = [];
        $scope.CategoryList = [];

        var editingFileName, isWorkingProject;

        $scope.templates = {
            properties: '/static/Templates/ProjectBrowser/properties.html',
            gridView: '/static/Templates/ProjectBrowser/gridView.html'
        };

        $scope.save = function() {
            if ($scope.file.saveAs.toLowerCase() == 'untitled') {
                surfToastr.error(appMessages.toastr.mapNamedAsUntitled($scope.file.saveAs));
                return;
            }
            var projectName = $scope.file.saveAs;
            var categoryId = $scope.file.categoryId;
            var organizationId = $scope.file.organizationId;
            var abstract = $scope.file.abstract;
            if (projectName && projectName.toLowerCase() == 'untitled') {
                surfToastr.error(appMessages.toastr.invalidMapName(projectName));
                // } 
                //else if (!helperService.isNameUnique(projectName, $scope)) {
                //     dialogBox.confirm({
                //         action: executeSave,
                //         text: appMessages.confirm.mapAlreadyExists(projectName)
                //     });
            } else /*if (subscriptionStatus.validateAddProject())*/ {
                executeSave(true);
            }

            function executeSave() {
                projectService.saveProject(projectName,abstract,organizationId,categoryId ).success(function(data) {
                    // projectService.executeAfterSuccessfulSave(data.layerIdToSavedDataIdMappings);
                    // subscriptionStatus.updateNumberOfProjects(data.numberOfProjects);
                    window.location = 'maps/' + data.id + '/view';
                });
                $modalInstance.close();
            }
        };
        function errorFn() {

        }
        //load User Profile
        function getUserProfile() {
            projectService.getUserProfile()
                .then(function(res) {
                    getUserOrganizationList(res.data.id);
                }, errorFn);
        }
        // Load organization list
        function getUserOrganizationList(userId) {
            projectService.getUserOrganizationList(userId)
                .then(function(res) {
                    $scope.UserOrganizationList = res.data.objects;
                }, errorFn);
        }
        
        // Load Category List
        function getCategoryList() {
            projectService.getCategoryList()
                .then(function(res) {
                    console.log(res);
                    $scope.CategoryList = res.data.objects;
                    
                }, errorFn);
        }
        function init(){
            getUserProfile();
            getCategoryList();
        }
        
        (init)();

        $scope.openProject = function() {
            if ($scope.project.showNameInput) {
                $scope.save();
                return;
            }

            if ($scope.selectedFile.Name == mapService.getMapName()) {
                surfToastr.error(appMessages.toastr.mapAlreadyOpen());
                return;
            }
            var selectionId = $scope.selectedFile.ProjectId;
            if (dirtyManager.isDirty()) {
                if (selectionId) {
                    dialogBox.multiAction({
                        text: appMessages.confirm.openNewMap,
                        actions: {
                            "Save": function() {
                                projectService.setAfterSave(function() {
                                    mapService.openWorkingMap(selectionId);
                                });
                                $rootScope.action.saveProject();
                                $modalInstance.close();
                            },
                            "Discard": function() {
                                mapService.openWorkingMap(selectionId);
                                $modalInstance.close();
                                dirtyManager.setDirty(false);
                            }
                        }
                    });
                }
            } else {
                mapService.openWorkingMap(selectionId);
                $modalInstance.close();
            }
        };

        $scope.openPublishDialog = function() {
            $modal.open({
                templateUrl: '/static/Templates/publishMapDialog.html',
                controller: 'publishMapDialogController',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    selectedMap: function() {
                        return $scope.selectedFile;
                    }
                }
            });
        };

        $scope.rename = function() {
            isWorkingProject = mapService.getMapName() == $scope.selectedFile.Name;
            $scope.editing = true;
            $scope.focus = true;
            editingFileName = $scope.selectedFile.Name;
        };
        $scope.download = function() {
            $window.open("/Project/Download?projectId=" + $scope.selectedFile.ProjectId);
        };
        $scope.deleteFile = function() {
            if ($scope.selectedFile.Name == mapService.getMapName()) {
                surfToastr.error(appMessages.toastr.cannotDeleteOpenMap());
                return;
            }
            var selectionId = $scope.selectedFile.ProjectId;
            if (selectionId) {
                dialogBox.confirm({
                    text: appMessages.confirm.deleteMap,
                    action: function() {
                        busyStateManager.showBusyState(appMessages.busyState.deleteItem);
                        $.post(urlResolver.resolveMap('Delete'), { projectId: selectionId }, function() {
                            surfToastr.success(appMessages.toastr.deleted($scope.selectedFile.Name));
                            $scope.removeSelectedFile();
                            subscriptionStatus.decreaseNumberOfProjects();
                            busyStateManager.hideBusyState();
                        });
                    },
                    width: "350px"
                });
            }
        };

        $scope.addFile = function(file) {
            $scope.$apply(function() {
                $scope.folders[0].files.push(file);
                if ($scope.selectedFolderName == $scope.folders[0].name) {
                    $scope.currentlyViewingFiles = $scope.folders[0].files;
                }
            });
        };

        $scope.removeSelectedFile = function() {
            $scope.$apply(function() {
                $scope.currentlyViewingFiles.splice($scope.currentlyViewingFiles.indexOf($scope.selectedFile), 1);
                $scope.selectedFile = {};
            });
        };

        $scope.setData = function(folders) {
            $scope.folders = folders;
            folders[0] && setSelected(folders[0]);
        };

        $scope.fetchData = function() {
            $http({ url: urlResolver.resolveMap('BrowserData'), method: 'GET' })
                .success(function(data) {
                    $scope.data.loading = false;
                    $scope.setData(data);
                }).error(function() {
                    $scope.data.loading = false;
                });
        };

        function setSelected(folder) {
            $scope.selectedFolderName = folder.name;
            $scope.currentlyViewingFiles = folder.files;
            $scope.selectedFile = {};
        }

        $scope.selectFolder = function(folder) {
            setSelected(folder);
        };

        $scope.selectMap = function(mapInfo) {
            if (mapInfo.IsLocked) {
                surfToastr.error(appMessages.toastr.mapLocked(), appMessages.toastr.upgradeRequiredTitle());
                return;
            }
            $scope.selectedFile = mapInfo;
            $scope.file.saveAs = mapInfo.Name;
        };

        var finishEditing = function(file) {
            $scope.editing = false;
            if (editingFileName == file.Name) {
                return;
            }
            var failed = helperService.renameMap($scope, file, urlResolver.resolveMap("Rename"));

            if (failed) {
                file.Name = editingFileName;
                $scope.editing = true;
            } else if (isWorkingProject) {
                mapService.setMapName(file.Name);
            }
        };

        $scope.stopEditing = function(file) {
            $scope.editing = false;
            if (!$scope.enter) {
                finishEditing(file);
            }
            $scope.enter = false;
        };

        $scope.saveIfEnterPressed = function(event, file) {
            if (event.keyCode == 13) {
                $scope.enter = true;
                finishEditing(file);
            }
        };

        $scope.closeDialog = function() {
            $modalInstance.close();
        };

        $scope.action = {
            doubleClick: function() {
                $scope.openProject();
            },
            click: function(data) {
                $scope.selectMap(data);
            }
        };
    }
]);
