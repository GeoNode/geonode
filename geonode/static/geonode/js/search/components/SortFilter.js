import React from "react";

const facetNodes = {
  default: (
    <ul className="dropdown-menu dropdown-menu-right" id="sort">
      <li>
        <a data-value="-date" data-filter="order_by" className="selected">
          {window.gettext("Most recent")}
        </a>
      </li>
      <li>
        <a data-value="date" data-filter="order_by">
          {window.gettext("Less recent")}
        </a>
      </li>
      <li>
        <a data-value="title" data-filter="order_by">
          {window.gettext("A - Z")}
        </a>
      </li>
      <li>
        <a data-value="-title" data-filter="order_by">
          {window.gettext("Z - A")}
        </a>
      </li>
      <li>
        <a data-value="-popular_count" data-filter="order_by">
          {window.gettext("Most popular")}
        </a>
      </li>
    </ul>
  ),
  groups: (
    <ul className="dropdown-menu dropdown-menu-right" id="sort">
      <li>
        <a
          data-value="-last_modified"
          data-filter="order_by"
          className="selected"
        >
          {window.gettext("Most recent")}
        </a>
      </li>
      <li>
        <a data-value="last_modified" data-filter="order_by">
          {window.gettext("Less recent")}
        </a>
      </li>
      <li>
        <a data-value="title" data-filter="order_by">
          {window.gettext("A - Z")}
        </a>
      </li>
      <li>
        <a data-value="-title" data-filter="order_by">
          {window.gettext("Z - A")}
        </a>
      </li>
    </ul>
  ),
  people: (
    <ul className="dropdown-menu dropdown-menu-right" id="sort">
      <li>
        <a
          data-value="-date_joined"
          data-filter="order_by"
          className="selected"
        >
          {window.gettext("Most recent")}
        </a>
      </li>
      <li>
        <a data-value="date_joined" data-filter="order_by">
          {window.gettext("Less recent")}
        </a>
      </li>
      <li>
        <a data-value="username" data-filter="order_by">
          {window.gettext("A - Z")}
        </a>
      </li>
      <li>
        <a data-value="-username" data-filter="order_by">
          {window.gettext("Z - A")}
        </a>
      </li>
    </ul>
  )
};

export default class SortFilter extends React.Component {
  searchFilter = window.djangoSearchVars.search_filter;
  state = {
    dataValue: "-date"
  };
  facetType = window.djangoSearchVars.facet_type;
  updateDataValue = dataValue => {
    console.log("!!!DATAVALUE", dataValue);
    this.setState({
      dataValue
    });
  };
  getStyle = dataValue => {
    if (dataValue instanceof Array) {
      for (let i = 0; i < dataValue.length; i += 1) {
        if (this.state.dataValue === dataValue[i]) return { display: "block" };
      }
    }
    if (this.state.dataValue === dataValue) return { display: "block" };
    return { display: "none" };
  };
  getFacetNode = () => {
    switch (this.facetType) {
      case "groups":
        return facetNodes.groups;
      case "people":
        return facetNodes.people;
      default:
        return facetNodes.default;
    }
  };
  render = () => {
    return (
      <div className="btn-group pull-right" role="group" aria-label="tools">
        <div className="btn-group" role="group">
          <button
            type="button"
            className="btn btn-default dropdown-toggle"
            data-toggle="dropdown"
            aria-haspopup="true"
            aria-expanded="false"
          >
            <div
              onClick={() => this.updateDataValue("title")}
              style={this.getStyle(["title", "username"])}
              ng-cloak
            >
              <i className="fa fa-sort-alpha-asc fa-lg" />
              <i className="fa fa-angle-down fa-lg" />
            </div>
            <div
              onClick={() => this.updateDataValue("-title")}
              style={this.getStyle(["-title", "-username"])}
              ng-cloak
            >
              <i className="fa fa-sort-alpha-desc fa-lg" />
              <i className="fa fa-angle-down fa-lg" />
            </div>
            <div
              style={this.getStyle(["date", "last_modified", "date_joined"])}
            >
              <i className="fa fa-clock-o" />
              <i className="fa fa-clock-o fa-level-up" />
              <i className="fa fa-angle-down fa-lg" />
            </div>
            <div
              style={this.getStyle(["-date", "-last_modified", "-date_joined"])}
            >
              <i className="fa fa-clock-o" />
              <i className="fa fa-clock-o fa-level-down" />
              <i className="fa fa-angle-down fa-lg" />
            </div>
            <div style={this.getStyle(["-popular_count"])} ng-cloak>
              <i className="fa fa-fire fa-lg" />
              <i className="fa fa-angle-down fa-lg" />
            </div>
            <div ng-if="dataValue == null" ng-cloak>
              <i className="fa fa-clock-o" />
              <i className="fa fa-clock-o fa-level-down" />
              <i className="fa fa-angle-down fa-lg" />
            </div>
          </button>
          {this.getFacetNode()}
        </div>
      </div>
    );
  };
}
