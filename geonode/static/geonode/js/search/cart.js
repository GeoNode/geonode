class Cart extends React.Component {
  constructor(cart) {
    super(cart);
    this.cart = cart;
  }

  getCart = () => {};

  getCartStyle = () => ({
    display: this.getCart().items.length ? "block" : "none"
  });

  fillCart = () => {
    // This will fail if angular<1.4.0
    let geonodeCart = null;
    try {
      geonodeCart = $cookies.getAll();
    } catch (err) {
      geonodeCart = null;
    }
    const cartSession = [];
    if (geonodeCart !== null) {
      if (Object.keys(geonodeCart).length > 1) {
        Object.keys(geonodeCart).forEach((key, index) => {
          if (key !== "csrftoken") {
            try {
              const obj = JSON.parse(geonodeCart[key]);
              obj.$$hashKey = `object:${index}`;
              if ("alternate" in obj) {
                cartSession.push(obj);
              }
            } catch (err) {
              console.log("Cart Session Issue: " + err.message);
            }
          }
        });
      }
    }
    return cartSession;
  };

  addItem = item => {
    if (!item.id && item.layer_identifier) {
      item.id = item.layer_identifier;
    }

    if (this.getItemById(item.id) === null) {
      this.getCart().items.push(item);
      // @TODO: $cookies.putObject(item["uuid"], item);
    }
  };

  removeItem = item => () => {
    if (this.getItemById(item.id) !== null) {
      const cart = this.getCart();
      angular.forEach(cart.items, (cartItem, index) => {
        if (cartItem.id === item.id) {
          cart.items.splice(index, 1);
          $cookies.remove(cartItem["uuid"]);
        }
      });
    }
  };

  toggleItem = item => {
    if (this.getItemById(item.id) === null) {
      this.addItem(item);
    } else {
      this.removeItem(item);
    }
  };

  getItemById = itemId => {
    const items = this.getCart().items;
    let returnItem = null;

    items.map(item => {
      if (item.id === itemId) {
        returnItem = item;
      }
    });

    return returnItem;
  };

  getFaClass = id => {
    if (this.getItemById(id) === null) {
      return "fa-plus";
    }
    return "fa-remove";
  };

  render = () => {
    return `
    <div id="composerCart" class="panel panel-default">
      <div
        class="panel-heading"
        ng-bind="'Selected ' + (facetType | default_if_blank : 'objects') | title "></div>
      <div
        style="{this.getCartStyle()}"
        class="panel-body">
        <p>Add {{ facetType | default_if_blank : 'objects' }} through the "checkboxes".</p>
      </div>
      <ul class="list-group">
        <li class="list-group-item clearfix" ng-if="resource && resource.title" ng-repeat="resource in cart.getCart().items">{{ resource.title | limitTo: 25}}{{ resource.title.length > 25 ? '...' : '' }}<button class="btn btn-default btn-xs pull-right" ng-click="cart.removeItem(resource)"><i class="fa fa-remove fa-lg"></i></button></li>
      </ul>
    </div>
    `;
  };
}

(function() {
  angular
    .module("cart", ["ngCookies"])
    .filter("title", function() {
      return function(value) {
        return value.replace(/\w\S*/g, function(txt) {
          return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
      };
    })
    .filter("default_if_blank", function() {
      return function(value, arg) {
        return angular.isString(value) && value.length > 0 ? value : arg;
      };
    })
    .controller("CartList", function($scope, cart) {
      $scope.cart = cart;
      $scope.layers_params = "";

      $scope.newMap = function() {
        var items = cart.getCart().items;
        var params = "";
        for (var i = 0; i < items.length; i++) {
          params += "layer=" + items[i].detail_url.split("/")[2] + "&";
        }
        window.location = siteUrl + "maps/new?" + params;
      };

      $scope.bulk_perms_submit = function() {
        var items = cart.getCart().items;
        var permissions = permissionsString($("#permission_form"), "base");
        var selected_ids = $.map(items, function(item) {
          return item.id;
        });
        var message = $("#bulk_perms_message");
        if (selected_ids.length == 0) {
          message
            .find(".message")
            .html("Please select at least one resource to set the permissions");
          message
            .addClass("alert-danger")
            .removeClass("alert-success alert-warning hidden");
          return;
        }
        $.ajax({
          type: "POST",
          url: siteUrl + "security/bulk-permissions",
          data: {
            permissions: JSON.stringify(permissions),
            resources: selected_ids
          },
          success: function(data) {
            var not_changed = $.parseJSON(data).not_changed;
            if (not_changed.length > 0) {
              message
                .find(".message")
                .html(
                  "Permissions correctly registered, although the following resources were" +
                    " skipped because you don't have the rights to edit their permissions:"
                );
              message.find(".extra_content").html(not_changed.join("</br>"));
              message
                .addClass("alert-warning")
                .removeClass("alert-success alert-danger hidden");
            } else {
              message
                .find(".message")
                .html("Permissions correctly registered.");
              message
                .addClass("alert-success")
                .removeClass("alert-warning alert-danger hidden");
            }
          },
          error: function(data) {
            message.find(".message").html($.parseJSON(data).error);
            message
              .addClass("alert-danger")
              .removeClass("alert-success alert-warning hidden");
          }
        });
      };
    })
    .directive("resourceCart", [
      function() {
        return {
          restrict: "EA",
          templateUrl: siteUrl + "static/geonode/js/templates/cart.html",
          link: function($scope, $element) {
            // Don't use isolateScope, but add to parent scope
            $scope.facetType = $element.attr("data-facet-type");
          }
        };
      }
    ])
    .service("cart", function($cookies) {
      this.init = function() {
        this.$cart = {
          items: this.fillCart()
        };
      };

      this.fillCart = function() {
        // This will fail if angular<1.4.0
        try {
          var geonodeCart = $cookies.getAll();
        } catch (err) {
          var geonodeCart = null;
        }
        var cartSession = [];
        if (geonodeCart !== null) {
          if (Object.keys(geonodeCart).length > 1) {
            Object.keys(geonodeCart).forEach(function(key, index) {
              if (key !== "csrftoken") {
                try {
                  var obj = JSON.parse(geonodeCart[key]);
                  obj["$$hashKey"] = "object:" + index;
                  if ("alternate" in obj) {
                    cartSession.push(obj);
                  }
                } catch (err) {
                  console.log("Cart Session Issue: " + err.message);
                }
              }
            });
          }
        }
        return cartSession;
      };

      this.getCart = function() {
        return this.$cart;
      };

      this.addItem = function(item) {
        if (!item.id && item.layer_identifier) {
          item.id = item.layer_identifier;
        }

        if (this.getItemById(item.id) === null) {
          this.getCart().items.push(item);
          $cookies.putObject(item["uuid"], item);
        }
      };

      this.removeItem = function(item) {
        if (this.getItemById(item.id) !== null) {
          var cart = this.getCart();
          angular.forEach(cart.items, function(cart_item, index) {
            if (cart_item.id === item.id) {
              cart.items.splice(index, 1);
              $cookies.remove(cart_item["uuid"]);
            }
          });
        }
      };

      this.toggleItem = function(item) {
        if (this.getItemById(item.id) === null) {
          this.addItem(item);
        } else {
          this.removeItem(item);
        }
      };

      this.getItemById = function(itemId) {
        var items = this.getCart().items;
        var the_item = null;
        angular.forEach(items, function(item) {
          if (item.id === itemId) {
            the_item = item;
          }
        });
        return the_item;
      };

      this.getFaClass = function(id) {
        if (this.getItemById(id) === null) {
          return "fa-plus";
        } else {
          return "fa-remove";
        }
      };
    })
    .run([
      "cart",
      function(cart) {
        cart.init();
      }
    ]);
})();
