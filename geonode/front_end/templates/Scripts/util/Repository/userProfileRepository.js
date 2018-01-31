repositoryModule.factory('userProfileRepository', [
    '$http', 'urlResolver',
    function($http, urlResolver) {
        function getUserSettings() {
            return $http.get(urlResolver.resolveUserProfile('GetUserSettings'));
        }

        function saveUserSettings(settings) {
            return $http.post(urlResolver.resolveUserProfile('SaveUserSettings'), settings);
        }

        function getUserProfile() {
            return $http.get('/people/current-user/');
        }

        function getUserOrganizationList(userId) {
            return $http.get('/api/user-organization-list/?user__id=' + userId);
        }


        return {
            getUserSettings: getUserSettings,
            saveUserSettings: saveUserSettings,
            getUserProfile: getUserProfile,
            getUserOrganizationList: getUserOrganizationList
        };
    }
]);