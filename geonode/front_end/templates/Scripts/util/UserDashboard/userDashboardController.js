userDashboardModule.controller("userDashboardController", ['$scope', 'userDashboardService', 'SubscriptionListService', 'surfToastr',
 function ($scope, userDashboardService, subscriptionListService, surfToastr) {

     $scope.profile = { Editable: false };
     $scope.userInfo = {};
     $scope.resourceUsageInfo = {};
     $scope.subscriptionInfo = {};
     var originalUserInfo = {};

     $scope.userInfoChanged = false;

     userDashboardService.getUserInfo().success(function (userInfo) {
         $scope.userInfo = angular.copy(userInfo);
         originalUserInfo = angular.copy(userInfo);
     }).error(function () {
     });

     userDashboardService.getSubscriptionInfo().success(function (subscriptionInfo) {
         $scope.subscriptionInfo = subscriptionInfo;
     }).error(function () {
     });

     userDashboardService.getResourceUsageInfo().success(function (usageInfo) {
         $scope.resourceUsageInfo = usageInfo;
     }).error(function () {
     });

     $scope.updateUserInfo = function () {
         userDashboardService.updateUserInfo($scope.userInfo).success(function (userInfo) {
             $scope.profile.Editable = false;
             originalUserInfo = angular.copy(userInfo);
             surfToastr.success(appMessages.toastr.userInfoUpdated());
         }).error(function () {
             surfToastr.success(appMessages.toastr.userInfoUpdateFailed());
         });
     };

     $scope.cancelProfileUpdate = function () {
         $scope.userInfo = angular.copy(originalUserInfo);
         $scope.profile.Editable = false;
     };

     $scope.regenerateSecretKey = function () {
         userDashboardService.getNewSecretKey().success(function(response) {
             $scope.userInfo.SecretApiKey = response.secretKey;
         });
     };

     $scope.phoneNumberPattern = (function () {
         var regexp = /^\(?(\d{3})\)?[ .-]?(\d{3})[ .-]?(\d{4})$/;
         return {
             test: function (value) {
                 if ($scope.requireTel === false) return true;
                 else return regexp.test(value);
             }
         };
     })();

     subscriptionListService.getSubscriptionHistory().success(function (subscriptions) {
         $scope.subscriptions = subscriptions;
     });
 }]);
