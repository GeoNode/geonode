import React, { Component } from 'react';
import Header from '../../components/organisms/header';
import GeonodeAnalytics from '../../components/organisms/geonode-analytics';
import GeonodeLayersAnalytics from '../../components/organisms/geonode-layers-analytics';
import WSAnalytics from '../../components/organisms/ws-analytics';
import WSLayersAnalytics from '../../components/organisms/ws-layers-analytics';
import MostActiveIPs from '../../components/organisms/most-active-ips';
import styles from './styles';


class SWPerf extends Component {
  render() {
    return (
      <div style={styles.root}>
        <Header />
        <div style={styles.analytics}>
          <GeonodeAnalytics />
          <WSAnalytics />
        </div>
        <div style={styles.analytics}>
          <GeonodeLayersAnalytics />
          <div style={styles.ws}>
            <WSLayersAnalytics />
            <MostActiveIPs />
          </div>
        </div>
      </div>
    );
  }
}


export default SWPerf;
