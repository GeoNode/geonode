import React, { Component } from 'react';
import Header from '../../components/organisms/header';
import GeonodeStatus from '../../components/organisms/geonode-status';
import GeoserverStatus from '../../components/organisms/geoserver-status';
import styles from './styles';


class HWPerf extends Component {
  render() {
    return (
      <div style={styles.root}>
        <Header />
        <div style={styles.analytics}>
          <GeonodeStatus />
          <GeoserverStatus />
        </div>
      </div>
    );
  }
}


export default HWPerf;
