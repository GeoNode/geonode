appModule.factory('helperService',
    ['surfToastr', '$timeout',
    function (surfToastr, $timeout) {
        return {
            isNameUnique: function (name, $scope) {
                var items = $scope.folders[0].files;
                for (var i in items) {
                    if (items[i].Name == name) {
                        return false;
                    }
                }
                return true;
            },
            canRename: function (name, $scope) {
                var items = $scope.folders[0].files;
                var count = 0;
                for (var i in items) {
                    if (items[i].Name == name) {
                        count++;
                        if (count > 1) {
                            return false;
                        }
                    }
                }
                return true;
            },
            rename: function ($scope, file, urlPostfix) {

                if (!file.Name) {
                    surfToastr.error(appMessages.toastr.blankName(), appMessages.toastr.unableToRenameTitle());
                    return true;
                }
                if (file.Type && file.Type.toLowerCase() == "project" && file.Name.toLowerCase() == "untitled") {
                    surfToastr.error(appMessages.toastr.mapNamedAsUntitled(file.Name));
                    return true;
                }
                if (!this.canRename(file.Name, $scope)) {
                    surfToastr.error(appMessages.toastr.duplicateName(), appMessages.toastr.unableToRenameTitle());
                    return true;
                }
                if (file.DataId) {
                    $.post(urlPostfix, { id: file.DataId, name: file.Name }, function (data) {
                        if (data) {
                            $timeout(function () {
                                angular.extend(file, data);
                            });
                        }
                        surfToastr.success(appMessages.toastr.nameChanged(file.Name));
                    });
                }
            },
            renameMap: function ($scope, map, urlPostfix) {
                if (!map.Name) {
                    surfToastr.error(appMessages.toastr.blankName(), appMessages.toastr.unableToRenameTitle());
                    return true;
                }
                if (map.Name.toLowerCase() == "untitled") {
                    surfToastr.error(appMessages.toastr.mapNamedAsUntitled(map.Name));
                    return true;
                }
                if (!this.canRename(map.Name, $scope)) {
                    surfToastr.error(appMessages.toastr.duplicateName(), appMessages.toastr.unableToRenameTitle());
                    return true;
                }
                if (map.ProjectId) {
                    $.post(urlPostfix, { id: map.ProjectId, name: map.Name }, function (updatedMap) {
                        if (updatedMap) {
                            $timeout(function () {
                                angular.extend(map, updatedMap);
                            });
                        }
                        surfToastr.success(appMessages.toastr.nameChanged(map.Name));
                    });
                }
            }
        };
    }]);
