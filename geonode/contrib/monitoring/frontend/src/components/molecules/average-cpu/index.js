import React from 'react';
import PropTypes from 'prop-types';
import CircularProgress from 'material-ui/CircularProgress';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class AverageCPU extends React.Component {
  static propTypes = {
    cpu: PropTypes.number,
  }

  static contextTypes = {
    muiTheme: PropTypes.object.isRequired,
  }

  render() {
    let cpu = this.props.cpu;
    if (cpu === undefined) {
      cpu = 'N/A';
    } else if (typeof cpu === 'number') {
      if (cpu === 0) {
        cpu = <CircularProgress size={this.context.muiTheme.spinner.size} />;
      } else {
        cpu += '%';
      }
    }
    return (
      <HoverPaper style={styles.content}>
        <h5>Average CPU</h5>
        <div style={styles.stat}>
          <h3>{cpu}</h3>
        </div>
      </HoverPaper>
    );
  }
}


export default AverageCPU;
