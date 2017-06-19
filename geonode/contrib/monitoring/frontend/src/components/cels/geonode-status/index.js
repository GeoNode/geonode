import React, { Component } from 'react';
import AverageCPU from '../../molecules/average-cpu';
import AverageMemory from '../../molecules/average-memory';
import styles from './styles';


class GeonodeStatus extends Component {
  render() {
    return (
      <div style={styles.content}>
        <h3>HOST 2</h3>
        <h5>GeoNode HW Status</h5>
        <div style={styles.geonode}>
          <AverageCPU cpu={40} />
          <AverageMemory memory={60} />
        </div>
      </div>
    );
  }
}


export default GeonodeStatus;
