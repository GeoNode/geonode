import React from "react";
import PropTypes from "prop-types";
import PubSub from "app/utils/pubsub";

export default class StatefulString extends React.Component {
  static propTypes = {
    id: PropTypes.string,
    default: PropTypes.string
  };
  constructor(props) {
    super(props);
    this.id = props.id;
    this.default = props.default;
    this.state = {
      content: this.default ? this.default : ""
    };
    PubSub.subscribe("syncView", (event, searchState) => {
      if (searchState[this.id] !== null && searchState[this.id] !== undefined) {
        this.setState({
          content: searchState[this.id]
        });
      }
    });
  }
  render = () => <span>{this.state.content}</span>;
}
