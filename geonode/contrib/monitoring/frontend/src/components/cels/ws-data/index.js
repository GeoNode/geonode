import React from 'react';
import AverageResponseTime from '../../molecules/average-response-time';
import MaxResponseTime from '../../molecules/max-response-time';
import TotalRequests from '../../molecules/total-requests';
import WSServiceSelect from '../../molecules/ws-service-select';
import styles from './styles';


class WSData extends React.Component {
  render() {
    return (
      <div style={styles.content}>
        <h5>W*S Data Overview</h5>
        <WSServiceSelect />
        <div style={styles.geonode}>
          <AverageResponseTime time={34} />
          <MaxResponseTime time={435} />
        </div>
        <TotalRequests requests={9} />
      </div>
    );
  }
}


export default WSData;
