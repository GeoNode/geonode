import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import AverageResponseTime from '../../molecules/average-response-time';
import MaxResponseTime from '../../molecules/max-response-time';
import TotalRequests from '../../molecules/total-requests';
import WSServiceSelect from '../../molecules/ws-service-select';
import { getResponseData } from '../../../utils';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  interval: state.interval.interval,
  response: state.wsServiceData.response,
  selected: state.wsService.service,
  timestamp: state.interval.timestamp,
  status: state.interval.status,
});


@connect(mapStateToProps, actions)
class WSData extends React.Component {
  static propTypes = {
    get: PropTypes.func.isRequired,
    interval: PropTypes.number,
    reset: PropTypes.func.isRequired,
    response: PropTypes.object,
    selected: PropTypes.string,
    timestamp: PropTypes.instanceOf(Date),
  }

  constructor(props) {
    super(props);

    this.get = (
        selected = this.props.selected,
        interval = this.props.interval,
    ) => {
      this.props.get(selected, interval);
    };
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.selected && nextProps.status === 'success') {
      if (
        this.props.selected !== nextProps.selected
        || nextProps.timestamp !== this.props.timestamp
      ) {
        this.get(
          nextProps.selected,
          nextProps.interval,
        );
      }
    }
  }

  componentWillUnmount() {
    this.props.reset();
  }

  render() {
    let averageResponseTime = 0;
    let maxResponseTime = 0;
    let totalRequests = 0;
    [
      averageResponseTime,
      maxResponseTime,
      totalRequests,
    ] = getResponseData(this.props.response);
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
