import React from 'react';
import PropTypes from 'prop-types';
import CircularProgress from 'material-ui/CircularProgress';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class AverageMemory extends React.Component {
  static propTypes = {
    mem: PropTypes.number,
  }

  static contextTypes = {
    muiTheme: PropTypes.object.isRequired,
  }

  render() {
    let mem = this.props.mem;
    if (mem === undefined) {
      mem = 'N/A';
    } else if (typeof mem === 'number') {
      if (mem === 0) {
        mem = <CircularProgress size={this.context.muiTheme.spinner.size} />;
      } else {
        mem += '%';
      }
    }
    return (
      <HoverPaper style={styles.content}>
        <h5>Average Memory</h5>
        <div style={styles.stat}>
          <h3>{mem}</h3>
        </div>
      </HoverPaper>
    );
  }
}


export default AverageMemory;
