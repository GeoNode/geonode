import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  from: state.interval.from,
  interval: state.interval.interval,
  response: state.geonodeAverageResponse.response,
  to: state.interval.to,
  uptime: state.uptime.response,
});


@connect(mapStateToProps, actions)
class Uptime extends React.Component {
  static propTypes = {
    style: PropTypes.object,
    get: PropTypes.func.isRequired,
    from: PropTypes.object,
    reset: PropTypes.func.isRequired,
    to: PropTypes.object,
    interval: PropTypes.number,
    uptime: PropTypes.object,
  }

  componentWillMount() {
    this.props.get(this.props.from, this.props.to, this.props.interval);
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps && nextProps.from && nextProps.from !== this.props.from
    ) {
      this.props.get(nextProps.from, nextProps.to, nextProps.interval);
    }
  }

  componentWillUnmount() {
    this.props.reset();
  }

  render() {
    const style = {
      ...styles.content,
      ...this.props.style,
    };
    let uptime = 0;
    if (this.props.uptime) {
      const data = this.props.uptime.data.data;
      if (data.length > 0) {
        if (data[0].data.length > 0) {
          const metric = data[0].data[0];
          /* uptime = metric.count;*/
        }
      }
    }
    return (
      <HoverPaper style={style}>
        <h3>Uptime</h3>
        <span style={styles.stat}>{uptime} days</span>
      </HoverPaper>
    );
  }
}


export default Uptime;
