import React from 'react';
import HoverPaper from '../../atoms/hover-paper';
import HR from '../../atoms/hr';
import ResponseTable from '../../cels/response-table';
import styles from './styles';


class WSLayerAnalytics extends React.Component {
  render() {
    return (
      <HoverPaper style={styles.content}>
        <h3>W*S Layers Analytics</h3>
        <HR />
        <ResponseTable
          average={10}
          max={50}
          requests={201}
          errorNumber={40}
        />
      </HoverPaper>
    );
  }
}


export default WSLayerAnalytics;
