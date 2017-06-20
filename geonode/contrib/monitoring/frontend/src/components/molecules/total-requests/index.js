import React from 'react';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class TotalRequests extends React.Component {
  static propTypes = {
    requests: React.PropTypes.number.isRequired,
  }

  render() {
    return (
      <HoverPaper style={styles.content}>
        <h5>Total Requests</h5>
        <div style={styles.stat}>
          <h3>{this.props.requests}</h3>
        </div>
      </HoverPaper>
    );
  }
}


export default TotalRequests;
