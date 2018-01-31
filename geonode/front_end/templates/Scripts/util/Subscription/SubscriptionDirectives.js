SubscriptionModule.directive("subscriptionFeature", [function () {
    return {
        restrict: 'A'
        , scope: {
            feature: '='
        }
        , templateUrl: './static/Templates/subscriptionFeature.html'
        , replace: true
    };
}]);

SubscriptionModule.directive("pricingScheme", ['surfToastr', function (surfToastr) {
    return {
        restrict: 'A'
        , scope: {
            pricingSchemes: '=',
            upgradableSchemes: '='
        }
        , templateUrl: './static/Templates/pricingScheme.html'
        , replace: true
        , controller: ['$scope', '$window', function ($scope, $window) {
            $scope.canChooseScheme = function (schemeId) {
                return !!$scope.upgradableSchemes[schemeId];
            };

            $scope.choosePlan = function (schemeId) {
                if ($scope.canChooseScheme(schemeId)) {
                    $window.location.href = '/Subscription/Bill?pricingSchemeId=' + schemeId;
                } else {
                    surfToastr.error(appMessages.toastr.downgradeFailed());
                }
            };
        }]
    };
}]);

SubscriptionModule.directive("priceDisplay", [
    function () {
        return {
            restrict: 'EA',
            scope: {
                pricingData: '=',
            },
            template:
                    '<div>' +
                    '<span class="plan-actualprice" ng-if="pricingData.ActualPrice != pricingData.DiscountedPrice">${{pricingData.ActualPrice}}</span>' +
                    '${{pricingData.DiscountedPrice}}' +
                    '</div>'
        }
    }
]);