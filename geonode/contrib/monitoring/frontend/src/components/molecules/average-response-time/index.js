import React from 'react';
import PropTypes from 'prop-types';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class AverageResponseTime extends React.Component {
  static propTypes = {
    time: PropTypes.number,
  }

  render() {
    let time = this.props.time;
    if (time === undefined) {
      time = 'N/A';
    } else if (typeof time === 'number') {
      time += ' ms';
    }
    return (
      <HoverPaper style={styles.content}>
        <h5>Average Response Time</h5>
        <div style={styles.stat}>
          <h3>{time}</h3>
        </div>
      </HoverPaper>
    );
  }
}


export default AverageResponseTime;
