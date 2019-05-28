import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


const mapStateToProps = (state) => ({
  alertList: state.alertList.response,
  errorList: state.errorList.response,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps)
class HealthCheck extends React.Component {
  static propTypes = {
    alertList: PropTypes.object,
    errorList: PropTypes.object,
    style: PropTypes.object,
    timestamp: PropTypes.instanceOf(Date),
  }

  render() {
    const alertList = this.props.alertList;
    const alertNumber = alertList && alertList.data
                      ? alertList.data.problems.length
                      : 0;
    const alertStyle = alertNumber > 0
                     ? { backgroundColor: '#ffa031', color: '#fff' }
                     : {};
    const errorNumber = this.props.errorList
                      ? this.props.errorList.exceptions.length
                      : 0;
    const errorStyle = errorNumber > 0
                     ? { backgroundColor: '#d12b2b', color: '#fff' }
                     : {};
    const style = {
      ...styles.content,
      ...this.props.style,
      ...alertStyle,
      ...errorStyle,
    };
    return (
      <HoverPaper style={style}>
        <h3>Health Check</h3>
        <div style={styles.stat}>
          {alertNumber} alerts<br />
          {errorNumber} errors
        </div>
      </HoverPaper>
    );
  }
}


export default HealthCheck;
