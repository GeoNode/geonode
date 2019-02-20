import React from "react";
import ReactDOM from "react-dom";
import Pagination from "app/search/components/Pagination";

export default () => {
  ReactDOM.render(
    <Pagination id="numberOfPages" />,
    document.getElementById(`render_searchPagination`)
  );
};
