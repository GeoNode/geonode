angular.module('userProfileModule', ['repositoryModule']).factory('userProfileService', [
    'userProfileRepository',
    function (repository) {
        var _userSettings = {};
        var _isDataLoaded = false;

        function loadData() {
            repository.getUserSettings().success(function (settings) {
                _userSettings = settings;
                _isDataLoaded = true;
            });
        }
        
        function getSetting(settingName) {
            return _userSettings[settingName];
        }

        function saveSetting(settingName, settingValue) {
            if (!_isDataLoaded) {
                return;
            }

            var oldValue = _userSettings[settingName];
            if (settingValue != oldValue) {
                _userSettings[settingName] = settingValue;
                repository.saveUserSettings(_userSettings).error(function () {
                    _userSettings[settingName] = oldValue;
                });
            }
        }

        function getUserProfile() {
            return repository.getUserProfile();
        }
        function getUserOrganizationList(userId) {
            return repository.getUserOrganizationList(userId);
        }

        return {
            getSetting: getSetting,
            saveSetting: saveSetting,
            loadData: loadData,
            getUserProfile: getUserProfile,
            getUserOrganizationList: getUserOrganizationList
        };
    }
]);