import React from 'react';
import PropTypes from 'prop-types';
import RaisedButton from 'material-ui/RaisedButton';
import ChartIcon from 'material-ui/svg-icons/av/equalizer';
import HoverPaper from '../../atoms/hover-paper';
import GeonodeData from '../../cels/geonode-data';
import WSData from '../../cels/ws-data';
import styles from './styles';


class SoftwarePerformance extends React.Component {
  static contextTypes = {
    router: PropTypes.object.isRequired,
  }

  constructor(props) {
    super(props);

    this.handleClick = () => {
      this.context.router.push('/performance/software');
    };
  }

  render() {
    return (
      <HoverPaper style={styles.content}>
        <div style={styles.header}>
          <h3 style={styles.title}>Software Performance</h3>
          <RaisedButton
            onClick={this.handleClick}
            style={styles.icon}
            icon={<ChartIcon />}
          />
        </div>
        <GeonodeData />
        <WSData />
      </HoverPaper>
    );
  }
}


export default SoftwarePerformance;
