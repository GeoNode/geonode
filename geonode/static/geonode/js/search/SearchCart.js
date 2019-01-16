import React from "react";
import cookies from "app/utils/cookies";

class CartListItem extends React.Component {
  render = () => (
    <li
      className="list-group-item clearfix"
      ng-if="resource && resource.title"
      ng-repeat="resource in cart.getCart().items"
    >
      <button
        className="btn btn-default btn-xs pull-right"
        ng-click="cart.removeItem(resource)"
      >
        <i className="fa fa-remove fa-lg" />
      </button>
    </li>
  );
}

class CartList extends React.Component {
  buildList = () => {};
  render = () => <ul className="list-group" />;
}

export default class Cart extends React.Component {
  constructor(cart) {
    super(cart);
    this.cart = cart;
  }

  getCart = () => {};

  getCartStyle = () => ({
    display: this.getCart() && this.getCart().items.length ? "block" : "none"
  });

  fillCart = () => {
    // This will fail if angular<1.4.0
    let geonodeCart = null;
    try {
      geonodeCart = cookies.getAll();
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
              // eslint-disable-next-line no-console
              console.warn(`Cart Session Issue: ${err.message}`);
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
          cookies.remove(cartItem.uuid);
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
    return items.filter(item => item.id === itemId)[0];
  };

  getFaClass = id => {
    if (this.getItemById(id) === null) {
      return "fa-plus";
    }
    return "fa-remove";
  };

  componentDidMount() {
    this.cart = {
      items: this.fillCart()
    };
    console.log("!!!THIS CART", this.cart);
  }

  render = () => (
    // @TODO: determine how to reconcile Django template syntax with React
    // components

    <div id="composerCart" className="panel panel-default">
      <div
        className="panel-heading"
        ng-bind="'Selected ' + (facetType | default_if_blank : 'objects') | title "
      />
      <div style={this.getCartStyle()} className="panel-body">
        <p>{`Add objects through the "checkboxes."`}</p>
      </div>
      <ul className="list-group">
        <li
          className="list-group-item clearfix"
          ng-if="resource && resource.title"
          ng-repeat="resource in cart.getCart().items"
        >
          <button
            className="btn btn-default btn-xs pull-right"
            ng-click="cart.removeItem(resource)"
          >
            <i className="fa fa-remove fa-lg" />
          </button>
        </li>
      </ul>
    </div>
  );
}
