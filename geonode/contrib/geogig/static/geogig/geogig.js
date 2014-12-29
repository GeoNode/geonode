'use strict';

(function() {

  var module = angular.module('geogig', []);
  var http, rootScope;
  var service_ = null;
  var q = null;


  module.service('geoGigService', function($q, $http) {
    return {
      geogigCommand: function(url) {
        var deferred = new $q.defer();
        if (url) {
          var request = url + '&callback=JSON_CALLBACK';
          $http.jsonp(request).success(function(data, status) {
            deferred.resolve(data);
          }).error(function(error) {
            deferred.reject(error);
          });
          return deferred.promise;
        }
      }
    };
  });

  /*
  * Main search controller
  * Load data from api and defines the multiple and single choice handlers
  * Syncs the browser url with the selections
  */
  module.controller('geogigController', function($scope, geogigConfig, geoGigService) {
    var errorText = 'There was an error receiving the latest GeoGig stats.';
    $scope.geoserverURL = geogigConfig.geoserverURL;
    $scope.workspace = geogigConfig.workspace;
    $scope.typename = geogigConfig.typename;
    $scope.store = geogigConfig.store;
    $scope.statisticsURL = geogigConfig.statisticsURL;
    $scope.logURL = geogigConfig.logURL;
    $scope.repoURL = geogigConfig.repoURL;

    if ($scope.statisticsURL) {
      geoGigService.geogigCommand($scope.statisticsURL).then(
          function(data) {
            if (data.response.success) {
              $scope.stats = data.response.Statistics;
              $('#geogig-message').hide();
              $('#geogig-stats').show();
            }
          },
          function(error) {
            $scope.error = error;
            $('#geogig-message > h4').text(errorText);
            console.log(error);
          });
    }

    if ($scope.logURL) {
      geoGigService.geogigCommand($scope.logURL).then(
          function(data) {
            if (data.response.success) {
              $('#geogig-message').hide();
              $('#geogig-stats').show();
              var response = data.response.commit;
              if (!Array.isArray(response)) {
                $scope.commits = [response];
              } else {
                $scope.commits = response;
              }
              for (var i = 0; i < $scope.commits.length; i++) {
                var commit = $scope.commits[i];
                if (commit.author) {
                  commit.commitTimeSince = moment().calendar(commit.author.timestamp);
                }
              }
            }
          },
          function(error) {
            $scope.error = error;
            $('#geogig-message > h4').text(errorText);
          });
    }

  });
})();
