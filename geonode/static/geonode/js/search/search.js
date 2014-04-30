'use strict';

(function(){

  var module = angular.module('main_search', [], function($locationProvider) {
      $locationProvider.html5Mode(true);

      // make sure that angular doesn't intercept the page links
      angular.element("a").prop("target", "_self");
    });

  module.controller('MainController', function($scope, $location, $http, Configs){
    $scope.query = $location.search();

    // Keep in sync the page location with the query object
    $scope.$watch('query', function(){
      $location.search($scope.query);
    }, true);
      
    //Get data from apis and make them available to the page
    $http.get(Configs.url).success(function(data){
      $scope.results = data.objects;
      $scope.results_meta = data.meta;
    });

    /*
    * Add the selection behavior to the element, it adds/removes the 'active' class
    * and pushes/removes the value of the element from the query object
    */
    $scope.multiple_choice_listener = function($event){    
      var element = $($event.target);
      var query_entry = [];
      var data_class = element.attr('data-class');

      // If the query object has the record then grab it 
      if ($scope.query.hasOwnProperty(data_class)){

        // When in the location are passed two filters of the same
        // type then they are put in an array otherwise is a single string
        if ($scope.query[data_class] instanceof Array){
          query_entry = $scope.query[data_class];
        }else{
          query_entry.push($scope.query[data_class]);
        }     
      }

      // If the element is active active then deactivate it
      if(element.hasClass('active')){
        // clear the active class from it
        element.removeClass('active');

        // Remove the entry from the correct query in scope
        var value = element.val();
        query_entry.splice(query_entry.indexOf(value), 1);
      }
      // if is not active then activate it
      else if(!element.hasClass('active')){
        // Add the entry in the correct query
        if (query_entry.indexOf(element.val()) == -1){
          query_entry.push(element.val());  
        }         
        element.addClass('active');
      }

      //save back the new query entry to the scope query
      $scope.query[data_class] = query_entry;

      //if the entry is empty then delete the property from the query
      if(query_entry.length == 0){
        delete($scope.query[data_class]);
      }
    }
  });
  
})();
