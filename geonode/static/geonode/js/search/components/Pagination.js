import React from "react";
import StatefulString from "app/search/components/StatefulString";
import searcher from "app/search/searcher";

export default function Pagination() {
  return (
    <div className="row">
      <nav>
        <ul className="pagination pull-right">
          <li onClick={searcher.paginateDown}>
            <a href="javascript:;">
              <strong>
                <i className="fa fa-angle-left" />
              </strong>
            </a>
          </li>
          <li>
            <a href="javascript:;">
              {window.gettext("page")} <StatefulString id="currentPage" />{" "}
              {window.gettext("of")} <StatefulString id="numberOfPages" />
            </a>
          </li>
          <li onClick={searcher.paginateUp}>
            <a href="javascript:;">
              <strong>
                <i className="fa fa-angle-right" />
              </strong>
            </a>
          </li>
        </ul>
      </nav>
    </div>
  );
}
