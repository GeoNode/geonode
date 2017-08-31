import React from 'react';
import PropTypes from 'prop-types';
import HR from '../../atoms/hr';
import styles from './styles';


class ResponseTable extends React.Component {
  static propTypes = {
    average: PropTypes.number,
    errorNumber: PropTypes.number,
    max: PropTypes.number,
    requests: PropTypes.number,
  }

  render() {
    const average = this.props.average ? `${this.props.average} ms` : 'N/A';
    const max = this.props.max ? `${this.props.max} ms` : 'N/A';
    const requests = this.props.requests || 0;
    return (
      <div style={styles.content}>
        <h4>Average Response Time {average}</h4>
        <HR />
        <h4>Max Response Time {max}</h4>
        <HR />
        <h4>Total Requests {requests}</h4>
        <HR />
        <h4>Total Errors {this.props.errorNumber}</h4>
      </div>
    );
  }
}


export default ResponseTable;
