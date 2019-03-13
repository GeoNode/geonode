import React from "react";

const facetData = {
  default: [
    {
      text: "Most recent",
      value: "-date",
      selected: true
    },
    {
      text: "Less recent",
      value: "date"
    },
    {
      text: "A - Z",
      value: "title"
    },
    {
      text: "Z - A",
      value: "-title"
    },
    {
      text: "Most popular",
      value: "-popular_count"
    }
  ],
  groups: [
    {
      text: "Most recent",
      value: "-date",
      selected: true
    },
    {
      text: "Less recent",
      value: "date"
    },
    {
      text: "A - Z",
      value: "title"
    },
    {
      text: "Z - A",
      value: "-title"
    }
  ],
  people: [
    {
      text: "Most recent",
      value: "-date",
      selected: true
    },
    {
      text: "Less recent",
      value: "date"
    },
    {
      text: "A - Z",
      value: "username"
    },
    {
      text: "Z - A",
      value: "-username"
    }
  ]
};

export default class SortFilter extends React.Component {
  searchFilter = window.djangoSearchVars.search_filter;
  state = {
    dataValue: "-date"
  };
  facetType = window.djangoSearchVars.facet_type;
  updateDataValue = dataValue => {
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
  buildFacetNode = nodes => {
    const liNodes = nodes.map((node, i) => (
      <li key={i}>
        <a
          href="javascript:;"
          onClick={() => this.updateDataValue(node.value)}
          data-value={node.value}
          data-filter="order_by"
          className={node.selected ? "selected" : ""}
        >
          {window.gettext(node.text)}
        </a>
      </li>
    ));
    return (
      <ul className="dropdown-menu dropdown-menu-right" id="sort">
        {liNodes}
      </ul>
    );
  };
  getFacetNode = () => {
    switch (this.facetType) {
      case "groups":
        return this.buildFacetNode(facetData.groups);
      case "people":
        return this.buildFacetNode(facetData.people);
      default:
        return this.buildFacetNode(facetData.default);
    }
  };
  render = () => (
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
          >
            <i className="fa fa-sort-alpha-asc fa-lg" />
            <i className="fa fa-angle-down fa-lg" />
          </div>
          <div
            onClick={() => this.updateDataValue("-title")}
            style={this.getStyle(["-title", "-username"])}
          >
            <i className="fa fa-sort-alpha-desc fa-lg" />
            <i className="fa fa-angle-down fa-lg" />
          </div>
          <div style={this.getStyle(["date", "last_modified", "date_joined"])}>
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
          <div style={this.getStyle(["-popular_count"])}>
            <i className="fa fa-fire fa-lg" />
            <i className="fa fa-angle-down fa-lg" />
          </div>
        </button>
        {this.getFacetNode()}
      </div>
    </div>
  );
}
