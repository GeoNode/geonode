angular.module('SubscriptionListModule', [])
.directive("subscriptionhistory", [
        function () {
            return {
                restrict: 'E',
                scope: {
                    subscriptions: '='
                },
                templateUrl: './static/Templates/subscriptionList.html',
                replace: true,
                controller: ['$scope', '$filter',
                    function ($scope, $filter) {
                        $scope.getDurationText = function (subscription) {
                            if (subscription.SubscriptionStatus == 'Running') {
                                return formatDate(subscription.StartOn) + ' to Now';
                            } else if (subscription.SubscriptionStatus == 'NotStarted') {
                                return 'Not yet';
                            } else {
                                if (!subscription.StartOn) {
                                    return 'Never';
                                } else {
                                    return formatDate(subscription.StartOn) + " to " + formatDate(subscription.EndOn);
                                }
                            }

                        };

                        var statusTextMap = {
                            'NotStarted': 'Not Started',
                            'Canceled': 'Canceled',
                            'Running': 'Active',
                            'Expired': 'Expired'
                        };

                        $scope.isRunning = function (subscription) {
                            return subscription.SubscriptionStatus == 'Running';
                        };

                        $scope.statusText = function(subscription) {
                            return statusTextMap[subscription.SubscriptionStatus];
                        };

                        $scope.priceText = function(subscription) {
                            return subscription.SubscriptionType == 'Free' ? 'Free' : "$" + subscription.Price;
                        };

                        function formatDate(date) {
                            return $filter('date')(date, 'dd MMMM, yyyy');
                        }

                        $scope.formatDate = formatDate;
                    }
                ]
            };
        }
]).factory('SubscriptionListService', ["$http", function ($http) {
    return {
        getUnExpiredSubscriptions: function () {
            return $http.get(window.urlRoot + 'UserProfile/GetUnExpiredSubscriptions');
        },
        getSubscriptionHistory: function () {
            return $http.get(window.urlRoot + 'UserProfile/GetSubscriptionHistory');
        }
    };
}]);