import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import AverageResponseTime from '../../molecules/average-response-time';
import MaxResponseTime from '../../molecules/max-response-time';
import TotalRequests from '../../molecules/total-requests';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  from: state.interval.from,
  interval: state.interval.interval,
  response: state.geonodeAverageResponse.response,
  to: state.interval.to,
});


@connect(mapStateToProps, actions)
class GeonodeData extends React.Component {
  static propTypes = {
    from: PropTypes.object,
    get: PropTypes.func.isRequired,
    reset: PropTypes.func.isRequired,
    response: PropTypes.object,
    to: PropTypes.object,
    interval: PropTypes.number,
  }

  componentWillMount() {
    this.props.get(this.props.from, this.props.to, this.props.interval);
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps && nextProps.from && nextProps.from !== this.props.from
    ) {
      this.props.get(nextProps.from, nextProps.to, nextProps.interval);
    }
  }

  componentWillUnmount() {
    this.props.reset();
  }

  render() {
    let averageResponseTime = 0;
    let maxResponseTime = 0;
    let totalRequests = 0;
    if (this.props.response) {
      averageResponseTime = undefined;
      maxResponseTime = undefined;
      totalRequests = undefined;
      const data = this.props.response.data.data;
      if (data.length > 0) {
        if (data[0].data.length > 0) {
          const metric = data[0].data[0];
          maxResponseTime = Math.floor(metric.max);
          averageResponseTime = Math.floor(metric.val);
          totalRequests = metric.count;
        }
      }
    }
    return (
      <div style={styles.content}>
        <h5>Geonode Data Overview</h5>
        <div style={styles.geonode}>
          <AverageResponseTime time={averageResponseTime} />
          <MaxResponseTime time={maxResponseTime} />
        </div>
        <TotalRequests requests={totalRequests} />
      </div>
    );
  }
}


export default GeonodeData;
