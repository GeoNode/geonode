import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import AverageCPU from '../../molecules/average-cpu';
import AverageMemory from '../../molecules/average-memory';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  from: state.interval.from,
  interval: state.interval.interval,
  response: state.geonodeAverageResponse.response,
  to: state.interval.to,
});


@connect(mapStateToProps, actions)
class GeonodeStatus extends React.Component {
  static propTypes = {
    from: PropTypes.object,
    get: PropTypes.func.isRequired,
    reset: PropTypes.func.isRequired,
    response: PropTypes.object,
    to: PropTypes.object,
    interval: PropTypes.number,
  }

  componentWillMount() {
    this.props.get(this.props.from, this.props.to, this.props.interval);
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
    let cpu = 0;
    if (this.props.response) {
      cpu = undefined;
      const data = this.props.response.data.data;
      if (data.length > 0) {
        if (data[0].data.length > 0) {
          const metric = data[0].data[0];
          cpu = Math.floor(metric.val);
        }
      }
    }
    return (
      <div style={styles.content}>
        <h3>HOST 1</h3>
        <h5>GeoNode HW Status</h5>
        <div style={styles.geonode}>
          <AverageCPU cpu={cpu} />
          <AverageMemory memory={60} />
        </div>
      </div>
    );
  }
}


export default GeonodeStatus;
