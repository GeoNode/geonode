import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import HoverPaper from '../../atoms/hover-paper';
import CPU from '../../cels/cpu';
import Memory from '../../cels/memory';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  cpu: state.geoserverCpuSequence.response,
  memory: state.geoserverMemorySequence.response,
  interval: state.interval.interval,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps, actions)
class GeoserverStatus extends React.Component {
  static propTypes = {
    cpu: PropTypes.object,
    getCpu: PropTypes.func.isRequired,
    getMemory: PropTypes.func.isRequired,
    memory: PropTypes.object,
    resetCpu: PropTypes.func.isRequired,
    resetMemory: PropTypes.func.isRequired,
    timestamp: PropTypes.instanceOf(Date),
    interval: PropTypes.number,
    half: PropTypes.bool,
  }

  static defaultProps = {
    half: true,
  }

  constructor(props) {
    super(props);
    this.get = (interval = this.props.interval) => {
      this.props.getCpu(interval);
      this.props.getMemory(interval);
    };

    this.reset = () => {
      this.props.resetCpu();
      this.props.resetMemory();
    };
  }

  componentWillMount() {
    this.get();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps) {
      if (nextProps.timestamp && nextProps.timestamp !== this.props.timestamp) {
        this.get(nextProps.interval);
      }
    }
  }

  componentWillUnmount() {
    this.reset();
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
    const contentStyle = this.props.half
                       ? styles.content
                       : { ...styles.content, width: '100%' };
    return (
      <HoverPaper style={contentStyle}>
        <h3>GeoServer status</h3>
        <div style={styles.stat}>
          <CPU cpu={5} data={cpuData} />
          <Memory memory={5} data={memoryData} />
        </div>
      </HoverPaper>
    );
  }
}


export default GeoserverStatus;
