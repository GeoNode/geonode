'use strict';

(function() {

  var module = angular.module('geogit', []);
  var http, rootScope;
  var service_ = null;
  var q = null;


  module.service('geoGitService', function($q, $http) {
    return {
      geogitCommand: function(url) {
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
  module.controller('geogitController', function($scope, geogitConfig, geoGitService) {
    var errorText = 'There was an error receiving the latest GeoGit stats.';
    $scope.geoserverURL = geogitConfig.geoserverURL;
    $scope.workspace = geogitConfig.workspace;
    $scope.typename = geogitConfig.typename;
    $scope.store = geogitConfig.store;
    $scope.statisticsURL = geogitConfig.statisticsURL;
    $scope.logURL = geogitConfig.logURL;
    $scope.repoURL = geogitConfig.repoURL;

    if ($scope.statisticsURL) {
      geoGitService.geogitCommand($scope.statisticsURL).then(
          function(data) {
            if (data.response.success) {
              $scope.stats = data.response.Statistics;
              $('#geogit-message').hide();
              $('#geogit-stats').show();
            }
          },
          function(error) {
            $scope.error = error;
            $('#geogit-message > h4').text(errorText);
            console.log(error);
          });
    }

    if ($scope.logURL) {
      geoGitService.geogitCommand($scope.logURL).then(
          function(data) {
            if (data.response.success) {
              $('#geogit-message').hide();
              $('#geogit-stats').show();
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
            $('#geogit-message > h4').text(errorText);
          });
    }

  });
})();
