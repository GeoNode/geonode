import React from 'react';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class MaxResponseTime extends React.Component {
  static propTypes = {
    time: React.PropTypes.number.isRequired,
  }

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


export default MaxResponseTime;
