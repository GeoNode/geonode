SubscriptionModule.factory('SubscriptionService', ["$http", function ($http) {
    return {
        getUserInfo: function () {
            return $http.get('../UserProfile/GetUserInfo');
        },
        getSubscriptionDetails: function () {
            return $http.get(window.urlRoot + 'Subscription/GetSubscriptionDetails');
        },
        getCurrentPricingScheme: function () {
            return $http.get(window.urlRoot + 'UserProfile/GetCurrentPricingScheme');
        },
        getUpgradablePricingSchemes: function () {
            return $http.get(window.urlRoot + 'UserProfile/GetUpgradablePricingSchemes');
        }
    };
} ]);