import React from 'react';
import HoverPaper from '../../components/atoms/hover-paper';
import Map from '../../components/atoms/map';
import Header from '../../components/organisms/header';
import Stats from '../../components/organisms/stats';
import SoftwarePerformance from '../../components/organisms/software-performance';
import HardwarePerformance from '../../components/organisms/hardware-performance';
import styles from './styles';


class Home extends React.Component {
  render() {
    return (
      <div style={styles.root}>
        <Header />
        <Stats />
        <div style={styles.content}>
          <SoftwarePerformance />
          <div style={styles.hardware}>
            <HardwarePerformance />
            <HoverPaper>
              <Map />
            </HoverPaper>
          </div>
        </div>
      </div>
    );
  }
}


export default Home;
