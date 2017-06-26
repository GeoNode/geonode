import React from 'react';
import Paper from 'material-ui/Paper';


class HoverPaper extends React.Component {
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


HoverPaper.propTypes = {
  children: React.PropTypes.node,
  style: React.PropTypes.object,
};


export default HoverPaper;
