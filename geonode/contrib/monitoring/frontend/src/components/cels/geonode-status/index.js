import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import AverageCPU from '../../molecules/average-cpu';
import AverageMemory from '../../molecules/average-memory';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  cpu: state.geonodeCpuStatus.response,
  mem: state.geonodeMemStatus.response,
  from: state.interval.from,
  interval: state.interval.interval,
  to: state.interval.to,
});


@connect(mapStateToProps, actions)
class GeonodeStatus extends React.Component {
  static propTypes = {
    cpu: PropTypes.object,
    from: PropTypes.object,
    getCpu: PropTypes.func.isRequired,
    getMem: PropTypes.func.isRequired,
    interval: PropTypes.number,
    mem: PropTypes.object,
    resetCpu: PropTypes.func.isRequired,
    resetMem: PropTypes.func.isRequired,
    to: PropTypes.object,
  }

  componentWillMount() {
    this.props.getCpu(this.props.from, this.props.to, this.props.interval);
    this.props.getMem(this.props.from, this.props.to, this.props.interval);
  }

  componentWillReceiveProps(nextProps) {
    if (
      nextProps &&
      nextProps.from &&
      nextProps.interval !== this.props.interval
    ) {
      this.props.getCpu(nextProps.from, nextProps.to, nextProps.interval);
      this.props.getMem(nextProps.from, nextProps.to, nextProps.interval);
    }
  }

  componentWillUnmount() {
    this.props.resetCpu();
    this.props.resetMem();
  }

  render() {
    let cpu = 0;
    if (this.props.cpu) {
      cpu = undefined;
      const data = this.props.cpu.data.data;
      if (data.length > 0) {
        if (data[0].data.length > 0) {
          const metric = data[0].data[0];
          cpu = Math.floor(metric.val);
        }
      }
    }
    let mem = 0;
    if (this.props.mem) {
      mem = undefined;
      const data = this.props.mem.data.data;
      if (data.length > 0) {
        if (data[0].data.length > 0) {
          const metric = data[0].data[0];
          mem = Math.floor(metric.val);
        }
      }
    }
    return (
      <div style={styles.content}>
        <h3>HOST 1</h3>
        <h5>GeoNode HW Status</h5>
        <div style={styles.geonode}>
          <AverageCPU cpu={cpu} />
          <AverageMemory mem={mem} />
        </div>
      </div>
    );
  }
}


export default GeonodeStatus;
