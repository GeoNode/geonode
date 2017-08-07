import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import AverageResponseTime from '../../molecules/average-response-time';
import MaxResponseTime from '../../molecules/max-response-time';
import TotalRequests from '../../molecules/total-requests';
import WSServiceSelect from '../../molecules/ws-service-select';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  from: state.interval.from,
  interval: state.interval.interval,
  selected: state.wsService.service,
  to: state.interval.to,
  response: state.wsServiceData.response,
});


@connect(mapStateToProps, actions)
class WSData extends React.Component {
  static propTypes = {
    get: PropTypes.func.isRequired,
    selected: PropTypes.string,
    from: PropTypes.object,
    interval: PropTypes.number,
    response: PropTypes.object,
    to: PropTypes.object,
  }

  constructor(props) {
    super(props);

    this.get = (
        from = this.props.from,
        to = this.props.to,
        interval = this.props.interval,
        selected = this.props.selected,
    ) => {
      this.props.get(from, to, interval, selected);
    };
  }

  componentWillReceiveProps(nextProps) {
    if (
      this.props.selected !== nextProps.selected
      || nextProps.from !== this.props.from
    ) {
      this.get();
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
      const d1length = data.length;
      if (d1length > 0) {
        const d2 = data[d1length - 1];
        const d2length = d2.data.length;
        if (d2length > 0) {
          const metric = d2.data[d2length - 1];
          maxResponseTime = Math.floor(metric.max);
          averageResponseTime = Math.floor(metric.val);
          totalRequests = metric.samples_count;
        }
      }
    }
    return (
      <div style={styles.content}>
        <h5>W*S Data Overview</h5>
        <WSServiceSelect />
        <div style={styles.geonode}>
          <AverageResponseTime time={averageResponseTime} />
          <MaxResponseTime time={maxResponseTime} />
        </div>
        <TotalRequests requests={totalRequests} />
      </div>
    );
  }
}


export default WSData;
