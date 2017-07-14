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
  data: state.geonodeResponseSequence.response,
});


@connect(mapStateToProps, actions)
class GeonodeAnalytics extends React.Component {
  static propTypes = {
    from: PropTypes.object,
    get: PropTypes.func.isRequired,
    reset: PropTypes.func.isRequired,
    to: PropTypes.object,
    data: PropTypes.object,
    interval: PropTypes.number,
  }

  componentWillMount() {
    this.props.get(this.props.from, this.props.to);
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps && nextProps.from && nextProps.from !== this.props.from) {
      this.props.get(nextProps.from, nextProps.to);
    }
  }

  render() {
    let responseData = [];
    let throughputData = [];
    let errorsRateData = [];
    if (this.props.data && this.props.data.data && this.props.data.data.data) {
      responseData = this.props.data.data.data.map(element => ({
        name: element.valid_from,
        time: element.data.length > 0 ? Math.floor(element.data[0].val) : 0,
      }));
    }
    return (
      <HoverPaper style={styles.content}>
        <h3>Geonode Analytics</h3>
        <ResponseTime average={5} max={10} last={8} data={responseData} />
        <HR />
        <Throughput total={5} data={throughputData} />
        <HR />
        <ErrorsRate errors={2} data={errorsRateData} />
      </HoverPaper>
    );
  }
}


export default GeonodeAnalytics;
