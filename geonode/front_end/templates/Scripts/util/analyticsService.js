(function() {
    angular
        .module('appModule')
        .service('analyticsService', analyticsService);

    analyticsService.$inject = ['$http', '$q', '$window', '$cookies'];

    function analyticsService($http, $q, $window, $cookies) {
        function get(url) {
            var deferred = $q.defer();
            $http.get(url)
                .success(function(res) {
                    deferred.resolve(res);
                }).error(function(error, status) {
                    deferred.reject({ error: error, status: status });
                });
            return deferred.promise;
        }

        function put(url, obj) {
            var deferred = $q.defer();
            $http.put(url, obj, {
                headers: {
                    "X-CSRFToken": $cookies.get('csrftoken')
                }
            }).success(function(res) {
                deferred.resolve(res);
            }).error(function(error, status) {
                deferred.reject({ error: error, status: status });
            });
            return deferred.promise;
        }

        function post(url, obj) {
            var deferred = $q.defer();
            $http.post(url, obj, {
                headers: {
                    "X-CSRFToken": $cookies.get('csrftoken')
                }
            }).success(function(res) {
                deferred.resolve(res);
            }).error(function(error, status) {
                deferred.reject({ error: error, status: status });
            });
            return deferred.promise;
        }
        angular.isUndefinedOrNull = function(val) {
            return angular.isUndefined(val) || val === null 
        };
        this.postGISAnalyticsToServer=function(url){
            var data=$window.localStorage.getItem('analytics-gis-data');
            if(data==null || angular.isUndefined(data)){
                $window.localStorage.setItem('analytics-gis-data',
                angular.toJson([]));
                return;
            }else{
                data=angular.fromJson(data);
                return post(url,data);
            }
        };
        this.saveGISAnalyticsToLocalStorage=function(data){
            var previousData=$window.localStorage.getItem('analytics-gis-data');
            if(angular.isUndefinedOrNull(previousData)){
                var initialData=[data];
                $window.localStorage.setItem('analytics-gis-data',
                angular.toJson(initialData));
            }else{
                previousData=angular.fromJson(previousData);
                previousData.push(data);
                $window.localStorage.setItem('analytics-gis-data',
                angular.toJson(previousData));
            }
        };
    }
})();