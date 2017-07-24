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
  autoRefresh: state.autoRefresh.autoRefresh,
  cpu: state.geonodeCpuSequence.response,
  from: state.interval.from,
  memory: state.geonodeMemorySequence.response,
  to: state.interval.to,
});


@connect(mapStateToProps, actions)
class GeonodeStatus extends React.Component {
  static propTypes = {
    autoRefresh: PropTypes.number,
    cpu: PropTypes.object,
    from: PropTypes.object,
    getCpu: PropTypes.func.isRequired,
    getMemory: PropTypes.func.isRequired,
    memory: PropTypes.object,
    resetCpu: PropTypes.func.isRequired,
    resetMemory: PropTypes.func.isRequired,
    to: PropTypes.object,
  }

  constructor(props) {
    super(props);
    this.get = (
      from = this.props.from,
      to = this.props.to,
    ) => {
      this.props.getCpu(from, to);
      this.props.getMemory(from, to);
    };

    this.reset = () => {
      this.props.resetCpu();
      this.props.resetMemory();
    };
  }

  componentWillMount() {
    this.get();
    if (this.props.autoRefresh && this.props.autoRefresh > 0) {
      this.intervalID = setInterval(this.get, this.props.autoRefresh);
    }
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps) {
      if (nextProps.from && nextProps.from !== this.props.from) {
        this.get(nextProps.from, nextProps.to);
      }
      if (nextProps.autoRefresh !== undefined) {
        if (nextProps.autoRefresh !== this.props.autoRefresh) {
          if (nextProps.autoRefresh > 0) {
            this.intervalID = setInterval(this.get, nextProps.autoRefresh);
          } else {
            clearInterval(this.intervalID);
            this.intervalID = undefined;
          }
        }
      }
    }
  }

  componentWillUnmount() {
    this.reset();
    if (this.intervalID) {
      clearInterval(this.intervalID);
      this.intervalID = undefined;
    }
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
