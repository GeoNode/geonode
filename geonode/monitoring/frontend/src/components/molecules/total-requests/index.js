import React from 'react';
import PropTypes from 'prop-types';
import CircularProgress from 'material-ui/CircularProgress';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class TotalRequests extends React.Component {
  static propTypes = {
    requests: PropTypes.number,
  }

  static contextTypes = {
    muiTheme: PropTypes.object.isRequired,
  }

  render() {
    let requests = this.props.requests;
    if (requests === undefined) {
      requests = 'N/A';
    } else if (typeof requests === 'number') {
      if (requests === 0) {
        requests = <CircularProgress size={this.context.muiTheme.spinner.size} />;
      }
    }
    return (
      <HoverPaper style={styles.content}>
        <h5>Total Requests</h5>
        <div style={styles.stat}>
          <h3>{requests}</h3>
        </div>
      </HoverPaper>
    );
  }
}


export default TotalRequests;
