'use strict';

(function(){
  angular.module('cart', [])
    .controller('CartList', function($scope, cart){
      $scope.cart = cart;
      $scope.layers_params = '';
  
      $scope.newMap = function(){
        var items = cart.getCart().items;
        var params = '';
        for(var i=0; i<items.length; i++){
          params += 'layer=' + items[i].detail_url.split('/')[2] +'&';
        }
        window.location = '/maps/new?' + params;
      }
    })

    .directive('resourceCart', [function(){
      return {
        restrict: 'E',
        templateUrl: "/static/geonode/js/templates/cart.html"
      };
    }])

    .service('cart', function(){
      
      this.init = function(){
        this.$cart = {
          items: []
        };
      };

      this.getCart = function(){
        return this.$cart;
      }

      this.addItem = function(item){
        if(this.getItemById(item.id) === null){
          this.getCart().items.push(item);
        }
      }

      this.removeItem = function(id){
        if(this.getItemById(id) !== null){
          var cart = this.getCart();
          angular.forEach(cart.items, function(item, index){
            if(item.id === id){
              cart.items.splice(index, 1);
            }
          });
        }
      }

      this.getItemById = function (itemId) {
        var items = this.getCart().items;
        var the_item = null;
        angular.forEach(items, function(item){
          if(item.id === itemId){
            the_item = item;
          }
        });
        return the_item;
      };
    })

    .run(['cart', function(cart){
      cart.init();
    }])
})();