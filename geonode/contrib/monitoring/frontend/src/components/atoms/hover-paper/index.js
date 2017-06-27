import React from 'react';
import PropTypes from 'prop-types';
import Paper from 'material-ui/Paper';


class HoverPaper extends React.Component {
  static propTypes = {
    children: PropTypes.node,
    style: PropTypes.object,
  }

  constructor(props) {
    super(props);

    this.state = {
      zDepth: 1,
    };

    this.handleMouseOver = () => {
      this.setState({ zDepth: 3 });
    };

    this.handleMouseOut = () => {
      this.setState({ zDepth: 1 });
    };
  }

  render() {
    return (
      <Paper
        style={this.props.style}
        onMouseOver={this.handleMouseOver}
        onMouseOut={this.handleMouseOut}
        zDepth={this.state.zDepth}
      >
        {this.props.children}
      </Paper>
    );
  }
}


export default HoverPaper;
