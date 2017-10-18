import React from 'react';
import PropTypes from 'prop-types';
import RaisedButton from 'material-ui/RaisedButton';
import ChartIcon from 'material-ui/svg-icons/av/equalizer';
import HoverPaper from '../../atoms/hover-paper';
import GeonodeStatus from '../../cels/geonode-status';
import GeoserverStatus from '../../cels/geoserver-status';
import styles from './styles';


class HardwarePerformance extends React.Component {
  static contextTypes = {
    router: PropTypes.object.isRequired,
  }

  constructor(props) {
    super(props);

    this.handleClick = () => {
      this.context.router.push('/performance/hardware');
    };
  }

  render() {
    return (
      <HoverPaper style={styles.content}>
        <div style={styles.header}>
          <h3 style={styles.title}>Hardware Performance</h3>
          <RaisedButton
            onClick={this.handleClick}
            style={styles.icon}
            icon={<ChartIcon />}
          />
        </div>
        <GeonodeStatus />
        <GeoserverStatus />
      </HoverPaper>
    );
  }
}


export default HardwarePerformance;
