import React from "react";
import PropTypes from "prop-types";

export default class MultiList extends React.Component {
  static propTypes = {
    selectors: PropTypes.array,
    name: PropTypes.string
  };
  constructor(props) {
    super(props);
    this.name = props.name;
    this.selectors = props.selectors;
  }
  render() {
    return (
      <div>
        <h4>
          <a href="#" className="toggle toggle-nav">
            <i className="fa fa-chevron-right" /> {this.name}
          </a>
        </h4>
        <ul className="nav closed" id="categories">
          {this.selectors}
        </ul>
      </div>
    );
  }
}
