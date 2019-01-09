import Cart from "app/search/SearchCart";
import React from "react";
import ReactDOM from "react-dom";

setTimeout(() => {
  ReactDOM.render(<Cart />, document.getElementById(`react-test`));
}, 1000);
