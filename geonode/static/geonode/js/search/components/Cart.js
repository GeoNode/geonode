import React from "react";
import getCartSession from "app/search/functions/getCartSession";
import cookies from "app/utils/cookies";
import getNewMapURL from "app/search/functions/getNewMapURL";
import ellipseString from "app/helpers/ellipseString";

export default class Cart extends React.Component {
  constructor() {
    super();
    this.cart = {
      items: this.fillCart()
    };
  }
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
  getLayerArray = () =>
    this.getCart().items.map(item => item.detail_url.split("/")[2]);
  openNewMap = () => {
    const layers = this.getLayerArray();
    window.location = getNewMapURL(window.siteUrl, layers);
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
  toggleItem = item => {
    if (this.getItemById(item.id) === null) {
      this.addItem(item);
    } else {
      this.removeItem(item);
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
  getFaClass = id => {
    if (this.getItemById(id) === null) {
      return "fa-plus";
    }
    return "fa-remove";
  };
  getCart = () => this.cart;
  getCartList = () =>
    this.getCart().items.map((resource, i) => {
      const style = {
        display: resource && resource.title ? "block" : "none"
      };
      return (
        <li className="list-group-item clearfix" style={style} key={i}>
          {ellipseString(resource.title, 25)}
          <button
            className="btn btn-default btn-xs pull-right"
            onClick={this.removeItem(resource)}
          >
            <i className="fa fa-remove fa-lg" />
          </button>
        </li>
      );
    });

  render = () => (
    <div id="composerCart" className="panel panel-default">
      <div
        className="panel-heading"
        ng-bind="'Selected ' + (facetType | default_if_blank : 'objects') | title "
      />
      <div ng-show="!cart.getCart().items.length" className="panel-body">
        <p>Add {window.facetType || "objects"} through the checkboxes.</p>
      </div>
      <ul className="list-group">{this.getCartList()}</ul>
    </div>
  );
}
