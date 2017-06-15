import React, { Component } from 'react';
import AverageResponseTime from '../../molecules/average-response-time';
import MaxResponseTime from '../../molecules/max-response-time';
import TotalRequests from '../../molecules/total-requests';
import styles from './styles';


class GeonodeData extends Component {
  render() {
    return (
      <div style={styles.content}>
        <h5>Geonode Data Overview</h5>
        <div style={styles.geonode}>
          <AverageResponseTime time={50} />
          <MaxResponseTime time={500} />
        </div>
        <TotalRequests requests={7} />
      </div>
    );
  }
}


export default GeonodeData;
