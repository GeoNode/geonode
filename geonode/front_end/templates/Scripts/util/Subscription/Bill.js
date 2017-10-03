var BillModule = angular.module("BillModule", []);

BillModule.factory('BillService', ["$http", function ($http) {
    return {
        getCountries: function () {
            return $http.get('/Subscription/CountryList');
        },

        getUsaStates: function () {
            return $http.get('/Subscription/UsaStateList');
        },

        getBill: function (pricingSchemeId) {
            return $http.get('/Subscription/GetBill?pricingSchemeId=' + pricingSchemeId);
        },

        getBillingInfo: function() {
            return $http.get('/Subscription/GetBillingInfo');
        }
    };
}]);

BillModule.controller('BillController', ['$scope', '$timeout', 'BillService',
    function ($scope, $timeout, service) {
        $scope.countryList = [];
        $scope.months = { "01": "January", "02": "February", "03": "March", "04": "April", "05": "May", "06": "June", "07": "July", "08": "August", "09": "September", "10": "October", "11": "November", "12": "December" };
        service.getCountries().success(function (countries) {
            $scope.countryList = countries;
        });

        $scope.isRenew = function () {
            if ($scope.Bill) {
                return $scope.Bill.FromScheme.SubscriptionType == $scope.Bill.ToScheme.SubscriptionType;
            }

            return false;
        };
       
        $scope.init = function (pricingSchemeId, country, state) {
            $scope.pricingSchemeId = pricingSchemeId;
            $scope.Country = country;
            $scope.State = state;
        }

        $scope.years = [];
        var currentYear = new Date().getFullYear();
        for (var i = 0; i < 5; i++) {
            $scope.years.push(currentYear + i);
        }

        service.getUsaStates().success(function (states) {
            $scope.usaStates = states;
        });

        $timeout(function () {
            service.getBill($scope.pricingSchemeId).success(function (bill) {
                $scope.Bill = bill;
            });
        });
        
        $scope.IsCountryUSA = function () {
            return $scope.Country == "United States";
        };
    }
]);