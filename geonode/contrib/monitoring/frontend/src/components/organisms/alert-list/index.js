import React from 'react';
import HoverPaper from '../../atoms/hover-paper';
import Alert from '../../cels/alert';
import styles from './styles';


class AlertList extends React.Component {
  render() {
    return (
      <HoverPaper style={styles.content}>
        <h3>Alerts</h3>
        <Alert
          date="05/29/2017 12:11:01"
          short="Geonode was not responding"
        />
        <Alert
          date="05/29/2017 12:07:32"
          short="Geonode served more than 10MB/m"
        />
      </HoverPaper>
    );
  }
}


export default AlertList;
