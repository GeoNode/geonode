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
  from: state.interval.from,
  to: state.interval.to,
  responses: state.geonodeResponseSequence.response,
  throughputs: state.geonodeThroughputSequence.throughput,
  errors: state.geonodeErrorSequence.response,
});


@connect(mapStateToProps, actions)
class GeonodeAnalytics extends React.Component {
  static propTypes = {
    from: PropTypes.object,
    getResponses: PropTypes.func.isRequired,
    getThroughputs: PropTypes.func.isRequired,
    getErrors: PropTypes.func.isRequired,
    resetResponses: PropTypes.func.isRequired,
    resetThroughputs: PropTypes.func.isRequired,
    resetErrors: PropTypes.func.isRequired,
    to: PropTypes.object,
    responses: PropTypes.object,
    throughputs: PropTypes.object,
    errors: PropTypes.object,
    interval: PropTypes.number,
  }

  componentWillMount() {
    this.props.getResponses(this.props.from, this.props.to);
    this.props.getThroughputs(this.props.from, this.props.to);
    this.props.getErrors(this.props.from, this.props.to);
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps && nextProps.from && nextProps.from !== this.props.from) {
      this.props.getResponses(nextProps.from, nextProps.to);
      this.props.getThroughputs(nextProps.from, nextProps.to);
      this.props.getErrors(nextProps.from, nextProps.to);
    }
  }

  componentWillUnmount() {
    this.props.resetResponses();
    this.props.resetThroughputs();
    this.props.resetErrors();
  }

  render() {
    let responseData = [];
    let throughputData = [];
    let errorRateData = [];
    if (this.props.responses && this.props.responses.data && this.props.responses.data.data) {
      responseData = this.props.responses.data.data.map(element => ({
        name: element.valid_from,
        time: element.data.length > 0 ? Math.floor(element.data[0].val) : 0,
      }));
    }
    if (this.props.throughputs && this.props.throughputs.data && this.props.throughputs.data.data) {
      throughputData = this.props.throughputs.data.data.map(element => ({
        name: element.valid_from,
        count: element.data.length > 0 ? Math.floor(element.data[0].val) : 0,
      }));
    }
    if (this.props.errors && this.props.errors.data && this.props.errors.data.data) {
      errorRateData = this.props.errors.data.data.map(element => ({
        name: element.valid_from,
        count: element.data.length > 0 ? Math.floor(element.data[0].val) : 0,
      }));
    }
    return (
      <HoverPaper style={styles.content}>
        <h3>Geonode Analytics</h3>
        <ResponseTime average={5} max={10} last={8} data={responseData} />
        <HR />
        <Throughput total={5} data={throughputData} />
        <HR />
        <ErrorsRate errors={2} data={errorRateData} />
      </HoverPaper>
    );
  }
}


export default GeonodeAnalytics;
