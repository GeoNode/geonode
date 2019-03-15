import React from "react";
import searcher from "app/search/searcher";
import PubSub from "app/utils/pubsub";
import getNewMapURL from "app/search/functions/getNewMapURL";
import getCartSession from "app/search/functions/getCartSession";
import cookies from "app/utils/cookies";

export default class Cart extends React.Component {
  fillCart = () => getCartSession(cookies.getAll());
  componentDidMount() {
    this.cart = {
      items: this.fillCart()
    };
  }
}
