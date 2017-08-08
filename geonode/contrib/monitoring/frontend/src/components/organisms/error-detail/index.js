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
    const errorData = this.props.errorDetails
                     ? this.props.errorDetails.error_data
                     : '';
    return (
      <HoverPaper style={styles.content}>
        <div style={styles.header}>
          <h3 style={styles.title}>Error {this.props.errorId}</h3>
        </div>
        {errorData}
      </HoverPaper>
    );
  }
}


export default ErrorDetail;
