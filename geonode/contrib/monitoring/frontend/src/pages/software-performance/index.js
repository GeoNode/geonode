import React from 'react';
import Header from '../../components/organisms/header';
import GeonodeAnalytics from '../../components/organisms/geonode-analytics';
import GeonodeLayersAnalytics from '../../components/organisms/geonode-layers-analytics';
import WSAnalytics from '../../components/organisms/ws-analytics';
import WSLayersAnalytics from '../../components/organisms/ws-layers-analytics';
import Map from '../../components/atoms/map';
import HoverPaper from '../../components/atoms/hover-paper';
import styles from './styles';


class SWPerf extends React.Component {
  render() {
    return (
      <div style={styles.root}>
        <Header back="/" />
        <div style={styles.analytics}>
          <GeonodeAnalytics />
          <WSAnalytics />
        </div>
        <div style={styles.analytics}>
          <GeonodeLayersAnalytics />
          <div style={styles.ws}>
            <WSLayersAnalytics />
            <HoverPaper>
              <Map />
            </HoverPaper>
          </div>
        </div>
      </div>
    );
  }
}


export default SWPerf;
