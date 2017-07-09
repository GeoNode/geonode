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

  constructor(props) {
    super(props);
    this.state = {
      averageResponseTime: 0,
      maxResponseTime: 0,
      totalRequests: 0,
    };
  }

  componentWillMount() {
    if (this.props && this.props.from) {
      this.props.get(this.props.from, this.props.to, this.props.interval);
    }
  }

  componentWillReceiveProps(nextProps) {
    if (
      nextProps &&
      nextProps.from &&
      nextProps.interval !== this.props.interval
    ) {
      this.props.get(nextProps.from, nextProps.to, nextProps.interval);
    }
  }

  componentWillUnmount() {
    this.props.reset();
  }

  render() {
    return (
      <div style={styles.content}>
        <h5>Geonode Data Overview</h5>
        <div style={styles.geonode}>
          <AverageResponseTime time={this.state.averageResponseTime} />
          <MaxResponseTime time={this.state.maxResponseTime} />
        </div>
        <TotalRequests requests={this.state.totalRequests} />
      </div>
    );
  }
}


export default GeonodeData;
