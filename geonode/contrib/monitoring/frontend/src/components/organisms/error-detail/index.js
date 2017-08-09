import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  errorDetails: state.errorDetails.response,
  from: state.interval.from,
  to: state.interval.to,
});


@connect(mapStateToProps, actions)
class ErrorDetail extends React.Component {
  static propTypes = {
    errorDetails: PropTypes.object,
    errorId: PropTypes.number,
    get: PropTypes.func.isRequired,
  }

  componentWillMount() {
    this.props.get(this.props.errorId);
  }

  render() {
    const errorDetails = this.props.errorDetails;
    const result = {};
    if (errorDetails) {
      result.date = `Date: ${errorDetails.created}`;
      result.service = `Service: ${errorDetails.service.name}`;
      result.errorType = `Type: ${errorDetails.error_type}`;
      result.errorData = errorDetails.error_data;
      if (errorDetails.request) {
        const request = errorDetails.request.request;
        const url = `${request.path}`;
        result.url = <span>URL: <a href={url}>{url}</a></span>;
        const response = errorDetails.request.response;
        result.errorCode = `Status code: ${response.status}`;
      }
    }
    return (
      <HoverPaper style={styles.content}>
        <div style={styles.header}>
          <h3 style={styles.title}>Error id: {this.props.errorId}</h3>
        </div>
        <div>{result.date}</div>
        <div>{result.service}</div>
        <div>{result.errorType}</div>
        <div>{result.errorCode}</div>
        <div>{result.url}</div>
        <pre>{result.errorData}</pre>
      </HoverPaper>
    );
  }
}


export default ErrorDetail;
