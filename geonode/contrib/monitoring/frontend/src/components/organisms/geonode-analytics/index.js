import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import HoverPaper from '../../atoms/hover-paper';
import HR from '../../atoms/hr';
import ResponseTime from '../../cels/response-time';
import Throughput from '../../cels/throughput';
import ErrorsRate from '../../cels/errors-rate';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  errors: state.geonodeErrorSequence.response,
  from: state.interval.from,
  interval: state.interval.interval,
  responseTimes: state.geonodeAverageResponse.response,
  responses: state.geonodeResponseSequence.response,
  throughputs: state.geonodeThroughputSequence.throughput,
  to: state.interval.to,
});


@connect(mapStateToProps, actions)
class GeonodeAnalytics extends React.Component {
  static propTypes = {
    errors: PropTypes.object,
    from: PropTypes.object,
    getErrors: PropTypes.func.isRequired,
    getResponseTimes: PropTypes.func.isRequired,
    getResponses: PropTypes.func.isRequired,
    getThroughputs: PropTypes.func.isRequired,
    interval: PropTypes.number,
    resetErrors: PropTypes.func.isRequired,
    resetResponseTimes: PropTypes.func.isRequired,
    resetResponses: PropTypes.func.isRequired,
    resetThroughputs: PropTypes.func.isRequired,
    responseTimes: PropTypes.object,
    responses: PropTypes.object,
    throughputs: PropTypes.object,
    to: PropTypes.object,
  }

  componentWillMount() {
    this.props.getResponses(this.props.from, this.props.to);
    this.props.getResponseTimes(
      this.props.from,
      this.props.to,
      this.props.interval,
    );
    this.props.getThroughputs(this.props.from, this.props.to);
    this.props.getErrors(this.props.from, this.props.to);
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps && nextProps.from && nextProps.from !== this.props.from) {
      this.props.getResponses(nextProps.from, nextProps.to);
      this.props.getResponseTimes(
        nextProps.from,
        nextProps.to,
        nextProps.interval,
      );
      this.props.getThroughputs(nextProps.from, nextProps.to);
      this.props.getErrors(nextProps.from, nextProps.to);
    }
  }

  componentWillUnmount() {
    this.props.resetResponses();
    this.props.resetResponseTimes();
    this.props.resetThroughputs();
    this.props.resetErrors();
  }

  render() {
    let responseData = [];
    let throughputData = [];
    let errorRateData = [];
    let averageResponseTime = 0;
    let maxResponseTime = 0;
    if (this.props.responseTimes) {
      const data = this.props.responseTimes.data.data;
      if (data.length > 0) {
        if (data[0].data.length > 0) {
          const metric = data[0].data[0];
          maxResponseTime = Math.floor(metric.max);
          averageResponseTime = Math.floor(metric.val);
        }
      }
    }
    if (
      this.props.responses
      && this.props.responses.data
      && this.props.responses.data.data
    ) {
      responseData = this.props.responses.data.data.map(element => ({
        name: element.valid_from,
        time: element.data.length > 0 ? Math.floor(element.data[0].val) : 0,
      }));
    }
    if (
      this.props.throughputs
      && this.props.throughputs.data
      && this.props.throughputs.data.data
    ) {
      throughputData = this.props.throughputs.data.data.map(element => ({
        name: element.valid_from,
        count: element.data.length > 0 ? Math.floor(element.data[0].val) : 0,
      }));
    }
    if (
      this.props.errors
      && this.props.errors.data
      && this.props.errors.data.data
    ) {
      errorRateData = this.props.errors.data.data.map(element => ({
        name: element.valid_from,
        count: element.data.length > 0 ? Math.floor(element.data[0].val) : 0,
      }));
    }
    return (
      <HoverPaper style={styles.content}>
        <h3>Geonode Analytics</h3>
        <ResponseTime
          average={averageResponseTime}
          max={maxResponseTime}
          data={responseData}
        />
        <HR />
        <Throughput data={throughputData} />
        <HR />
        <ErrorsRate data={errorRateData} />
      </HoverPaper>
    );
  }
}


export default GeonodeAnalytics;
