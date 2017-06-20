import React from 'react';
import HoverPaper from '../../atoms/hover-paper';
import HR from '../../atoms/hr';
import styles from './styles';


class WSAnalytics extends React.Component {
  render() {
    return (
      <HoverPaper style={styles.content}>
        <h3>W*S Layers Analytics</h3>
        <HR />
        <h4>Average Response Time #### ms</h4>
        <HR />
        <h4>Max Response Time #### ms</h4>
        <HR />
        <h4>Total Requests ####</h4>
        <HR />
        <h4>Total Errors ####</h4>
      </HoverPaper>
    );
  }
}


export default WSAnalytics;
