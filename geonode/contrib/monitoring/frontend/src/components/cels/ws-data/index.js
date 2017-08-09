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
  from: state.interval.from,
  interval: state.interval.interval,
  selected: state.wsService.service,
  to: state.interval.to,
  response: state.wsServiceData.response,
});


@connect(mapStateToProps, actions)
class WSData extends React.Component {
  static propTypes = {
    from: PropTypes.object,
    get: PropTypes.func.isRequired,
    interval: PropTypes.number,
    reset: PropTypes.func.isRequired,
    response: PropTypes.object,
    selected: PropTypes.string,
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

  componentWillMount() {
    this.get();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.selected) {
      if (
        this.props.selected !== nextProps.selected
        || nextProps.from !== this.props.from
      ) {
        this.get(
          nextProps.from,
          nextProps.to,
          nextProps.interval,
          nextProps.selected,
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
