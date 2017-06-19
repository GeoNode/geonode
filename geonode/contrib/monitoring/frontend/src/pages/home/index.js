import React, { Component } from 'react';
import Header from '../../components/organisms/header';
import Stats from '../../components/organisms/stats';
import SoftwarePerformance from '../../components/organisms/software-performance';
import HardwarePerformance from '../../components/organisms/hardware-performance';
import Map from '../../components/organisms/map';
import styles from './styles';


class Home extends Component {
  render() {
    return (
      <div style={styles.root}>
        <Header />
        <Stats />
        <div style={styles.content}>
          <SoftwarePerformance />
          <div style={styles.hardware}>
            <HardwarePerformance />
            <Map />
          </div>
        </div>
      </div>
    );
  }
}


export default Home;
