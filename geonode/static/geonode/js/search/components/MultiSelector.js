import React from "react";
import PropTypes from "prop-types";
import PubSub from "app/utils/pubsub";

export default class MultiSelector extends React.Component {
  static propTypes = {
    filter: PropTypes.string,
    model: PropTypes.object
  };
  constructor(props) {
    super(props);
    this.model = props.model;
    this.filter = props.filter;
    this.state = {
      selected: false
    };
  }
  getClassName = () => (this.state.selected ? "active" : "");
  toggleClass = () => {
    this.setState({
      selected: !this.state.selected
    });
  };

  query = () => {
    const data = {
      selectionType: !this.state.selected ? "select" : "unselect",
      value: this.model.name,
      filter: this.filter
    };
    PubSub.publish("multiSelectClicked", data);
    this.toggleClass();
  };

  getName = name => {
    let newName = "";
    newName += name.slice(0, 25);
    if (name.length > 25) return `${newName}...`;
    return newName;
  };

  render = () => (
    <li>
      <a
        data-value={this.model.slug}
        data-filter={this.filter}
        onClick={this.query}
        className={this.getClassName()}
      >
        {this.getName(this.model.name)}
        <span className="badge pull-right">{this.model.count}</span>
      </a>
    </li>
  );
}
