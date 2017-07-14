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
        const mbMem = (mem / 1024 / 1024);
        let mbMemFormated;
        if (mbMem < 10) {
          mbMemFormated = mbMem.toFixed(2);
        } else if (mbMem < 100) {
          mbMemFormated = mbMem.toFixed(1);
        } else {
          mbMemFormated = Math.floor(mbMem);
        }
        mem = `${mbMemFormated} MB`;
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
