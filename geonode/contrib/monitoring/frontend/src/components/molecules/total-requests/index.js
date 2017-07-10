import React from 'react';
import PropTypes from 'prop-types';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class TotalRequests extends React.Component {
  static propTypes = {
    requests: PropTypes.number,
  }

  render() {
    let requests = this.props.requests;
    if (requests === undefined) {
      requests = 'N/A';
    }
    return (
      <HoverPaper style={styles.content}>
        <h5>Total Requests</h5>
        <div style={styles.stat}>
          <h3>{requests}</h3>
        </div>
      </HoverPaper>
    );
  }
}


export default TotalRequests;
