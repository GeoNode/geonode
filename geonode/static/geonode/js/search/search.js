'use strict';

(function(){

  var module = angular.module('main_search', [], function($locationProvider) {
      $locationProvider.html5Mode(true);

      // make sure that angular doesn't intercept the page links
      angular.element("a").prop("target", "_self");
    });

  module.run(function($http, $rootScope){
    var params = typeof FILTER_TYPE == 'undefined' ? {} : {'type': FILTER_TYPE};
    $http.get(CATEGORIES_ENDPOINT, {params: params}).success(function(data){
      $rootScope.categories = data.objects;
    });

    $http.get(KEYWORDS_ENDPOINT, {params: params}).success(function(data){
      $rootScope.keywords = data.objects;
    });
  });

  module.controller('MainController', function($scope, $location, $http, Configs){
    $scope.query = $location.search();
    
    // Keep in sync the page location with the query object
    $scope.$watch('query', function(){
      $location.search($scope.query);
    }, true);
      
    //Get data from apis and make them available to the page
    function query_api(data){
      $http.get(Configs.url, {params: data || {}}).success(function(data){
        $scope.results = data.objects;
      });
    };
    query_api();

    /*
    * Add the selection behavior to the element, it adds/removes the 'active' class
    * and pushes/removes the value of the element from the query object
    */
    $scope.multiple_choice_listener = function($event){    
      var element = $($event.target);
      var query_entry = [];
      var data_filter = element.attr('data-filter');
      var value = element.attr('data-value');

      // If the query object has the record then grab it 
      if ($scope.query.hasOwnProperty(data_filter)){

        // When in the location are passed two filters of the same
        // type then they are put in an array otherwise is a single string
        if ($scope.query[data_filter] instanceof Array){
          query_entry = $scope.query[data_filter];
        }else{
          query_entry.push($scope.query[data_filter]);
        }     
      }

      // If the element is active active then deactivate it
      if(element.hasClass('active')){
        // clear the active class from it
        element.removeClass('active');

        // Remove the entry from the correct query in scope
        
        query_entry.splice(query_entry.indexOf(value), 1);
      }
      // if is not active then activate it
      else if(!element.hasClass('active')){
        // Add the entry in the correct query
        if (query_entry.indexOf(value) == -1){
          query_entry.push(value);  
        }         
        element.addClass('active');
      }

      //save back the new query entry to the scope query
      $scope.query[data_filter] = query_entry;

      //if the entry is empty then delete the property from the query
      if(query_entry.length == 0){
        delete($scope.query[data_filter]);
      }
      query_api($scope.query);
    }
  });
  
})();
