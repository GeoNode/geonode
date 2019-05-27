import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import HoverPaper from '../../atoms/hover-paper';
import actions from '../../organisms/alert-list/actions';
import styles from './styles';


const mapStateToProps = (state) => ({
  alertList: state.alertList.response,
  interval: state.interval.interval,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps, actions)
class Alerts extends React.Component {
  static propTypes = {
    alertList: PropTypes.object,
    get: PropTypes.func.isRequired,
    interval: PropTypes.number,
    style: PropTypes.object,
    timestamp: PropTypes.instanceOf(Date),
  }

  static contextTypes = {
    router: PropTypes.object.isRequired,
  }

  constructor(props) {
    super(props);

    this.handleClick = () => {
      this.context.router.push('/alerts');
    };

    this.get = (interval = this.props.interval) => {
      this.props.get(interval);
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

  render() {
    const alertList = this.props.alertList;
    const alertNumber = alertList && alertList.data
                      ? alertList.data.problems.length
                      : 0;
    const extraStyle = alertNumber > 0
                     ? { backgroundColor: '#ffa031', color: '#fff' }
                     : {};
    const style = {
      ...styles.content,
      ...this.props.style,
      ...extraStyle,
    };
    return (
      <HoverPaper style={style}>
        <div onClick={this.handleClick} style={styles.clickable}>
          <h3>Alerts</h3>
          <span style={styles.stat}>{alertNumber} Alerts to show</span>
        </div>
      </HoverPaper>
    );
  }
}


export default Alerts;
