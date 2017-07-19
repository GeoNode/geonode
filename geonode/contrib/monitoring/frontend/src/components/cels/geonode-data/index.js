import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import AverageResponseTime from '../../molecules/average-response-time';
import MaxResponseTime from '../../molecules/max-response-time';
import TotalRequests from '../../molecules/total-requests';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  autoRefresh: state.autoRefresh.autoRefresh,
  from: state.interval.from,
  interval: state.interval.interval,
  response: state.geonodeAverageResponse.response,
  to: state.interval.to,
});


@connect(mapStateToProps, actions)
class GeonodeData extends React.Component {
  static propTypes = {
    autoRefresh: PropTypes.number,
    from: PropTypes.object,
    get: PropTypes.func.isRequired,
    interval: PropTypes.number,
    reset: PropTypes.func.isRequired,
    response: PropTypes.object,
    to: PropTypes.object,
  }

  constructor(props) {
    super(props);
    this.get = (
      from = this.props.from,
      to = this.props.to,
      interval = this.props.interval,
    ) => {
      this.props.get(from, to, interval);
    };
  }

  componentWillMount() {
    this.get();
    if (this.props.autoRefresh && this.props.autoRefresh > 0) {
      this.intervalID = setInterval(this.get, this.props.autoRefresh);
    }
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps) {
      if (nextProps.from && nextProps.from !== this.props.from) {
        this.get(nextProps.from, nextProps.to, nextProps.interval);
      }
      if (nextProps.autoRefresh !== undefined) {
        if (nextProps.autoRefresh !== this.props.autoRefresh) {
          if (nextProps.autoRefresh > 0) {
            this.intervalID = setInterval(this.get, nextProps.autoRefresh);
          } else {
            clearInterval(this.intervalID);
            this.intervalID = undefined;
          }
        }
      }
    }
  }

  componentWillUnmount() {
    this.props.reset();
    if (this.intervalID) {
      clearInterval(this.intervalID);
      this.intervalID = undefined;
    }
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
