import React from 'react';
import PropTypes from 'prop-types';
import CircularProgress from 'material-ui/CircularProgress';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class AverageResponseTime extends React.Component {
  static propTypes = {
    time: PropTypes.number,
  }

  static contextTypes = {
    muiTheme: PropTypes.object.isRequired,
  }

  render() {
    let time = this.props.time;
    if (time === undefined) {
      time = 'N/A';
    } else if (typeof time === 'number') {
      if (time === 0) {
        time = <CircularProgress size={this.context.muiTheme.spinner.size} />;
      } else {
        time += ' ms';
      }
    }
    return (
      <HoverPaper style={styles.content}>
        <h5>Average Response Time</h5>
        <div style={styles.stat}>
          <h3>{time}</h3>
        </div>
      </HoverPaper>
    );
  }
}


export default AverageResponseTime;
