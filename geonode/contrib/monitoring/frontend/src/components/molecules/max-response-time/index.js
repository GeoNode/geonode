import React, { Component } from 'react';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class MaxResponseTime extends Component {
  render() {
    return (
      <HoverPaper style={styles.content}>
        <h5>Max Response Time</h5>
        <div style={styles.stat}>
          <h3>{this.props.time} ms</h3>
        </div>
      </HoverPaper>
    );
  }
}


MaxResponseTime.propTypes = {
  time: React.PropTypes.number.isRequired,
};


export default MaxResponseTime;
