import React, { Component } from 'react';
import HoverPaper from '../../atoms/hover-paper';
import GeonodeData from '../../cels/geonode-data';
import WSData from '../../cels/ws-data';
import ChartIcon from 'material-ui/svg-icons/av/equalizer';
import styles from './styles';


class SoftwarePerformance extends Component {
  render() {
    return (
      <HoverPaper style={styles.content}>
        <h3 style={styles.title}>Software Performance</h3>
        <ChartIcon />
        <GeonodeData />
        <WSData />
      </HoverPaper>
    );
  }
}


export default SoftwarePerformance;
