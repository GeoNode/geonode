SubscriptionModule.controller("SubscriptionController", ["$scope", "SubscriptionService", "SubscriptionListService", function ($scope, service, subscriptionListService) {
    $scope.subscriptionDetails = {};
    $scope.currentPricingScheme = {};
    $scope.upgradableSchemes = {};
    
    service.getSubscriptionDetails().success(function (subscriptionDetails) {
        $scope.subscriptionDetails = subscriptionDetails;
    });

    service.getCurrentPricingScheme().success(function (currentPricingScheme) {
        $scope.currentPricingScheme = currentPricingScheme;
    });

    service.getUpgradablePricingSchemes().success(function (upgradableSchemeIds) {
        $scope.upgradableSchemes = {};
        angular.forEach(upgradableSchemeIds, function (value) {
            $scope.upgradableSchemes[value] = true;
        });
    });

    service.getUserInfo().success(function (userInfo) {
        $scope.userInfo = userInfo;
    });

    subscriptionListService.getSubscriptionHistory().success(function (subscriptions) {
        $scope.subscriptions = subscriptions;
    });
} ]);