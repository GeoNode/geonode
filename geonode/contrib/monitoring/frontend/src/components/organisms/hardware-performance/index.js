import React, { Component } from 'react';
import HoverPaper from '../../atoms/hover-paper';
import GeonodeStatus from '../../cels/geonode-status';
import GeoserverStatus from '../../cels/geoserver-status';
import ChartIcon from 'material-ui/svg-icons/av/equalizer';
import styles from './styles';


class HardwarePerformance extends Component {
  render() {
    return (
      <HoverPaper style={styles.content}>
        <h3 style={styles.title}>Hardware Performance</h3>
        <ChartIcon />
        <GeonodeStatus />
        <GeoserverStatus />
      </HoverPaper>
    );
  }
}


export default HardwarePerformance;
