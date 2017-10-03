appModule.controller('shareDataController', ['$scope', 'selectedDataId', 'catalogDataService', '$modalInstance', 'surfToastr',
    function ($scope, selectedDataId, catalogDataService, $modalInstance, surfToastr) {
        var userStates = {};
        var initialSharedEmails = [];
        $scope.search = { username: "", email: "" };
        $scope.shareInfoChanged = false;

        catalogDataService.getSharingDataModel(selectedDataId).success(function (model) {
            $scope.ShareInfo = model;
            for (var i = 0; i < model.SharedEmails.length; i++) {
                initialSharedEmails.push(model.SharedEmails[i]);
            }

        }).error(function () {
        });

        function getUserState(user) {
            return userStates[user.Id];
        }

        function setUserState(user, status) {
            if (!status) {
                delete userStates[user.Id];
            } else {
                userStates[user.Id] = status;
            }
        }

        $scope.canWrite = false;

        $scope.makeSharedWithEmail = function (isEmailValid) {
            if ($scope.search.email == "" || !isEmailValid) {
                surfToastr.error(appMessages.toastr.invalidEmail());
                return;
            }
            if (!isAlreadySharedWithThisEmail($scope.search.email)) {
                $scope.ShareInfo.SharedEmails.push($scope.search.email);
                $scope.shareInfoChanged = true;
            } else {
                surfToastr.error(appMessages.toastr.duplicateEmail());
            }
            
            $scope.search.email = '';
        };

        $scope.makeUnsharedWithEmail = function (index) {
            $scope.ShareInfo.SharedEmails.splice(index, 1);
            $scope.shareInfoChanged = true;
        };

        var isAlreadySharedWithThisEmail = function (email) {
            for (var i in $scope.ShareInfo.SharedEmails) {
                if ($scope.ShareInfo.SharedEmails[i] == email) return true;
            }
            return false;
        };

        $scope.makeSharedWithUser = function (user) {
            $scope.ShareInfo.SharedUsers.push(user);
            removeUser($scope.ShareInfo.NonSharedUsers, user);
            $scope.shareInfoChanged = true;
            setUserState(user, getUserState(user) == 'Deleted' ? null : 'Added');
        };

        $scope.makeUnSharedWithUser = function (user) {
            $scope.shareInfoChanged = true;
            $scope.ShareInfo.NonSharedUsers.push(user);
            removeUser($scope.ShareInfo.SharedUsers, user);
            setUserState(user, getUserState(user) == 'Added' ? null : 'Deleted');
        };

        $scope.hideList = true;

        $scope.modalClicked = function (e) {
            $scope.hideList = true;
        };

        $scope.searchBoxFocused = function (e) {
            $scope.hideList = false;
            e.stopPropagation();
        };

        function removeUser(list, user) {
            for (var i = 0; i < list.length; i++) {
                if (list[i].Id == user.Id) {
                    list.splice(i, 1);
                }
            }
        }

        var getEmailStates = function () {
            var emailStates = [];

            for (var k = 0; k < $scope.ShareInfo.SharedEmails.length; k++) {
                if (!isContainedInTheList($scope.ShareInfo.SharedEmails[k], initialSharedEmails)) {
                    emailStates.push({ Email: $scope.ShareInfo.SharedEmails[k], State: "Added" });
                }
            }

            for (var m = 0 ; m < initialSharedEmails.length; m++) {
                if (!isContainedInTheList(initialSharedEmails[m], $scope.ShareInfo.SharedEmails)) {
                    emailStates.push({ Email: initialSharedEmails[m], State: "Deleted" });
                }
            }

            return emailStates;
        };

        var isContainedInTheList = function (searchItem, list) {
            for (var l = 0 ; l < list.length; l++) {
                if (list[l] == searchItem) {
                    return true;
                }
            }
            return false;
        };

        $scope.isSaving = false;

        $scope.saveChanges = function () {
            if ($scope.isSaving) {
                return false;
            }
            
            $scope.isSaving = true;
            busyStateManager.showBusyState(appMessages.busyState.save);

            var userSharedStates = [];
            var emailShareStates = getEmailStates();
            for (var id in userStates) {
                userSharedStates.push({ Id: id, State: userStates[id] });
            }
            catalogDataService.postSharing($scope.ShareInfo.DataId, userSharedStates, emailShareStates).success(function (response) {
                if (response.success) {
                    $modalInstance.close(response.isShared);
                    surfToastr.success(appMessages.toastr.changesSaved());
                } else {
                    surfToastr.error(appMessages.toastr.unableToSave());
                }
            }).error(function () {
                surfToastr.error(appMessages.toastr.saveError());
            }).finally(function() {
                $scope.isSaving = false;
                busyStateManager.hideBusyState();
            });
        };

        $scope.closeDialog = function () {
            $modalInstance.close();
        };
    }]);
