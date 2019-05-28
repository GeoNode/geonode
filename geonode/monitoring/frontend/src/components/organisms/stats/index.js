import React from 'react';
import HealthCheck from '../../cels/health-check';
import Uptime from '../../cels/uptime';
import Alerts from '../../cels/alerts';
import Errors from '../../cels/errors';
import styles from './styles';


class Stats extends React.Component {
  render() {
    return (
      <div style={styles.content}>
        <div style={styles.first}>
          <HealthCheck />
          <Uptime />
        </div>
        <div style={styles.second}>
          <Alerts />
          <Errors />
        </div>
      </div>
    );
  }
}


export default Stats;
