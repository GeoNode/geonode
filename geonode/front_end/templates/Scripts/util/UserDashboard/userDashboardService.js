userDashboardModule.factory('userDashboardService', ['$http', function ($http) {
    var baseUrl = window.urlRoot + 'UserProfile/';
    return {
        getResourceUsageInfo: function () {
            return $http.get(baseUrl + 'GetResourceUsageInfo');
        },
        getSubscriptionInfo: function () {
            return $http.get(baseUrl + 'GetSubscriptionInfo');
        },
        getUserInfo: function () {
            return $http.get(baseUrl + 'GetUserInfo');
        },
        updateUserInfo: function (userInfo) {
            return $http.post(baseUrl + "UpdateUserInfo", userInfo);
        },
        getNewSecretKey: function getNewSecretKey() {
            return $http.get(baseUrl + "GetNewSecretKey");
        }
    };
}]);