import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import HoverPaper from '../../atoms/hover-paper';
import HR from '../../atoms/hr';
import CPU from '../../cels/cpu';
import Memory from '../../cels/memory';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  cpu: state.geonodeCpuSequence.response,
  from: state.interval.from,
  memory: state.geonodeMemorySequence.response,
  to: state.interval.to,
});


@connect(mapStateToProps, actions)
class GeonodeStatus extends React.Component {
  static propTypes = {
    cpu: PropTypes.object,
    from: PropTypes.object,
    getCpu: PropTypes.func.isRequired,
    getMemory: PropTypes.func.isRequired,
    memory: PropTypes.object,
    resetCpu: PropTypes.func.isRequired,
    resetMemory: PropTypes.func.isRequired,
    to: PropTypes.object,
  }

  componentWillMount() {
    this.props.getCpu(this.props.from, this.props.to);
    this.props.getMemory(this.props.from, this.props.to);
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps && nextProps.from && nextProps.from !== this.props.from) {
      this.props.getCpu(nextProps.from, nextProps.to);
      this.props.getMemory(nextProps.from, nextProps.to);
    }
  }

  componentWillUnmount() {
    this.props.resetCpu();
    this.props.resetMemory();
  }

  render() {
    let cpuData = [];
    let memoryData = [];
    if (
      this.props.cpu
      && this.props.cpu.data
      && this.props.cpu.data.data
    ) {
      cpuData = this.props.cpu.data.data.map(element => ({
        name: element.valid_from,
        percents: element.data.length > 0 ? Math.floor(element.data[0].val) : 0,
      }));
    }
    if (
      this.props.memory
      && this.props.memory.data
      && this.props.memory.data.data
    ) {
      memoryData = this.props.memory.data.data.map(element => ({
        name: element.valid_from,
        MB: element.data.length > 0 ? element.data[0].val / 1024 / 1024 : 0,
      }));
    }
    return (
      <HoverPaper style={styles.content}>
        <h3>Geonode status</h3>
        <CPU cpu={5} data={cpuData} />
        <HR />
        <Memory memory={5} data={memoryData} />
      </HoverPaper>
    );
  }
}


export default GeonodeStatus;
