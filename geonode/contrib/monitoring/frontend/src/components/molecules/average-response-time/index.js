import React from 'react';
import PropTypes from 'prop-types';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class AverageResponseTime extends React.Component {
  static propTypes = {
    time: PropTypes.number.isRequired,
  }

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


export default AverageResponseTime;
