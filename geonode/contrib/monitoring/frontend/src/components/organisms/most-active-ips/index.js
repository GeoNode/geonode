import React from 'react';
import HoverPaper from '../../atoms/hover-paper';
import Map from '../../atoms/map';
import styles from './styles';


class MostActiveIPs extends React.Component {
  render() {
    return (
      <HoverPaper style={styles.content}>
        <h3>Most Active IPs</h3>
        <div style={styles.map}>
          <Map />
        </div>
      </HoverPaper>
    );
  }
}


export default MostActiveIPs;
