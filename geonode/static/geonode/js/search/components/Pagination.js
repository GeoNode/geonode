import React from "react";
import StatefulString from "app/search/components/StatefulString";

export default function Pagination() {
  return (
    <div className="row">
      <nav>
        <ul className="pagination pull-right">
          <li ng-click="paginate_down()">
            <a href>
              <strong>
                <i className="fa fa-angle-left" />
              </strong>
            </a>
          </li>
          <li>
            <a href>
              page <StatefulString id="currentPage" /> of{" "}
              <StatefulString id="numberOfPages" />
            </a>
          </li>
          <li ng-click="paginate_up()">
            <a href>
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
