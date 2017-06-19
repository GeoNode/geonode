import React, { Component } from 'react';
import AverageCPU from '../../molecules/average-cpu';
import AverageMemory from '../../molecules/average-memory';
import styles from './styles';


class GeoserverStatus extends Component {
  render() {
    return (
      <div style={styles.content}>
        <h3>HOST 2</h3>
        <h5>GeoServer HW Status</h5>
        <div style={styles.geonode}>
          <AverageCPU cpu={30} />
          <AverageMemory memory={50} />
        </div>
      </div>
    );
  }
}


export default GeoserverStatus;
