repositoryModule.factory('userProfileRepository', [
    '$http', 'urlResolver',
    function ($http, urlResolver) {
        function getUserSettings() {
            return $http.get(urlResolver.resolveUserProfile('GetUserSettings'));
        }

        function saveUserSettings(settings) {
            return $http.post(urlResolver.resolveUserProfile('SaveUserSettings'), settings);
        }

        return {
            getUserSettings: getUserSettings,
            saveUserSettings: saveUserSettings
        };
    }
]);