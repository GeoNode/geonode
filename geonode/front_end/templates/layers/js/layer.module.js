(function(){
    angular.module('LayerApp', [])
    .config(function($interpolateProvider, $locationProvider) {
        $interpolateProvider.startSymbol('[{');
        $interpolateProvider.endSymbol('}]');
        $locationProvider.html5Mode(true); 
    });
})()