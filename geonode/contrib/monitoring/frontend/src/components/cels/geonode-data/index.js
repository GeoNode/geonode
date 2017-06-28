import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import AverageResponseTime from '../../molecules/average-response-time';
import MaxResponseTime from '../../molecules/max-response-time';
import TotalRequests from '../../molecules/total-requests';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  responses: state.geonodeAverageResponse.response,
});


@connect(mapStateToProps, actions)
class GeonodeData extends React.Component {
  static propTypes = {
    get: PropTypes.func.isRequired,
    reset: PropTypes.func.isRequired,
    responses: PropTypes.object,
  }

  static defaultProps = {
    responses: {
      data: {
        data: [],
      },
    },
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
    this.props.get();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.responses) {
      let totalRequests = 0;
      let maxResponseTime = 0;
      let totalTimes = 0;
      nextProps.responses.data.data.forEach((response) => {
        if (response.data.length > 0) {
          response.data.forEach((element) => {
            totalRequests += element.count;
            totalTimes += element.count * element.val;
            const max = Number(element.max);
            if (maxResponseTime < max) {
              maxResponseTime = max;
            }
          });
        }
      });
      const averageResponseTime = Math.floor(totalTimes / totalRequests);
      this.setState({
        averageResponseTime,
        maxResponseTime,
        totalRequests,
      });
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
