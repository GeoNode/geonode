SubscriptionModule.controller("PricingController", ["$scope", "SubscriptionService", function ($scope, service) {
    $scope.subscriptionDetails = {};

    service.getSubscriptionDetails().success(function (subscriptionDetails) {
        $scope.subscriptionDetails = subscriptionDetails;
        $scope.basicPricing = subscriptionDetails.Basic.PricingSchemes[0];
        $scope.standardPricing = subscriptionDetails.Standard.PricingSchemes[0];
    });

    $scope.hasSpatialOffer = function(pricing) {
        return pricing && pricing.ActualPrice != pricing.DiscountedPrice;
    };
}]);