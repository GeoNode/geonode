import React, { Component } from 'react';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class AverageResponseTime extends Component {
  render() {
    return (
      <HoverPaper style={styles.content}>
        <h5>Average Response Time</h5>
        <div style={styles.stat}>
          <h3>{this.props.time} ms</h3>
        </div>
      </HoverPaper>
    );
  }
}


AverageResponseTime.propTypes = {
  time: React.PropTypes.number.isRequired,
};


export default AverageResponseTime;
