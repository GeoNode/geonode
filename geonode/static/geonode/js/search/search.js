'use strict';

(function(){

  var module = angular.module('main_search', []);

  module.controller('MainSearch', function($scope, $rootScope, $http, Configs){
    $http.get(Configs.url).success(function(data){
      $scope.results = data.objects;
      $rootScope.results_meta = data.meta;
    });
  });
})();

