import React from "react";
import getCartSession from "app/search/functions/getCartSession";
import cookies from "app/utils/cookies";

export default class Cart extends React.Component {
  fillCart = () => getCartSession(cookies.getAll());
  addItem = item => {
    if (!item.id && item.layer_identifier) {
      item.id = item.layer_identifier;
    }

    if (this.getItemById(item.id) === null) {
      this.getCart().items.push(item);
      cookies.storeCookie(item["uuid"], item);
    }
  };
  getItemById = itemId => {
    const items = this.getCart().items;
    for (let i = 0; i < items.length; i += 1) {
      if (items[i].id === itemId) {
        return items[i];
      }
    }
    return false;
  };
  removeItem = item => {
    if (this.getItemById(item.id) !== null) {
      const cart = this.getCart();
      for (let i = 0; i < cart.items; i += 1) {
        if (cart.items[i].id === item.id) {
          cart.items.splice(i, 1);
          cookies.remove(cart.items[i]["uuid"]);
        }
      }
    }
  };
  getCart = () => this.cart;
  componentDidMount() {
    this.cart = {
      items: this.fillCart()
    };
  }
}
