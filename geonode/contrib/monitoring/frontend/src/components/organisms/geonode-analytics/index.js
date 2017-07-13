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


const data = [
  { name: 'Page A', uv: 4000, pv: 2400, amt: 2400 },
  { name: 'Page B', uv: 3000, pv: 1398, amt: 2210 },
  { name: 'Page C', uv: 2000, pv: 9800, amt: 2290 },
  { name: 'Page D', uv: 2780, pv: 3908, amt: 2000 },
  { name: 'Page E', uv: 1890, pv: 4800, amt: 2181 },
  { name: 'Page F', uv: 2390, pv: 3800, amt: 2500 },
  { name: 'Page G', uv: 3490, pv: 4300, amt: 2100 },
];


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
        <Throughput total={5} data={data} />
        <HR />
        <ErrorsRate errors={2} data={data} />
      </HoverPaper>
    );
  }
}


export default GeonodeAnalytics;
