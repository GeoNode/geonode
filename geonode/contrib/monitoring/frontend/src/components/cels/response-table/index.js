import React from 'react';
import PropTypes from 'prop-types';
import HR from '../../atoms/hr';
import styles from './styles';


class ResponseTable extends React.Component {
  static propTypes = {
    average: PropTypes.number.isRequired,
    errorNumber: PropTypes.number.isRequired,
    max: PropTypes.number.isRequired,
    requests: PropTypes.number.isRequired,
  }

  render() {
    return (
      <div style={styles.content}>
        <h4>Average Response Time {this.props.average} ms</h4>
        <HR />
        <h4>Max Response Time {this.props.max} ms</h4>
        <HR />
        <h4>Total Requests {this.props.requests}</h4>
        <HR />
        <h4>Total Errors {this.props.errorNumber}</h4>
      </div>
    );
  }
}


export default ResponseTable;
