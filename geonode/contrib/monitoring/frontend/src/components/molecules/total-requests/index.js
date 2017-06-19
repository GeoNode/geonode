import React, { Component } from 'react';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class TotalRequests extends Component {
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


TotalRequests.propTypes = {
  requests: React.PropTypes.number.isRequired,
};


export default TotalRequests;
