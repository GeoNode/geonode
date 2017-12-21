(function() {
    angular.module('SystemSettingsApp', ['ngCookies'])
        .config(['$interpolateProvider', '$locationProvider', function($interpolateProvider, $locationProvider) {
            $interpolateProvider.startSymbol('[{');
            $interpolateProvider.endSymbol('}]');
            $locationProvider.html5Mode(true);
        }]);
})();

