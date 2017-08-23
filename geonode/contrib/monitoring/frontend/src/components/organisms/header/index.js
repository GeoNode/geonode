import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import RaisedButton from 'material-ui/RaisedButton';
import AutorefreshIcon from 'material-ui/svg-icons/action/autorenew';
import Back from 'material-ui/svg-icons/image/navigate-before';
/* import { formatHeaderDate } from '../../../utils';*/
import { minute, hour, day, week } from '../../../constants';
import actions from './actions';
import styles from './styles';
import { AUTO_REFRESH_INTERVAL } from './constants';


const mapStateToProps = (state) => ({
  interval: state.interval.interval,
});


@connect(mapStateToProps, actions)
class Header extends React.Component {
  static contextTypes = {
    router: PropTypes.object.isRequired,
  }

  static propTypes = {
    autoRefresh: PropTypes.bool,
    back: PropTypes.string,
    disableInterval: PropTypes.bool,
    interval: PropTypes.number,
    setInterval: PropTypes.func.isRequired,
  }

  static defaultProps = {
    autoRefresh: true,
  }

  constructor(props) {
    super(props);

    this.state = {
      autoRefresh: false,
    };

    this.get = (interval = this.props.interval) => {
      this.props.setInterval(interval);
    };

    this.handleMinute = () => {
      const interval = 10 * minute;
      this.props.setInterval(interval);
    };

    this.handleHour = () => {
      this.props.setInterval(hour);
    };

    this.handleDay = () => {
      this.props.setInterval(day);
    };

    this.handleWeek = () => {
      this.props.setInterval(week);
    };

    this.handleAutoRefresh = () => {
      if (this.state.autoRefresh) {
        clearInterval(this.intervalID);
        this.intervalID = undefined;
        this.setState({ autoRefresh: false });
      } else {
        this.intervalID = setInterval(this.get, AUTO_REFRESH_INTERVAL);
        this.get();
        this.setState({ autoRefresh: true });
      }
    };
  }

  componentWillReceiveProps(nextProps) {
    if (this.intervalID) {
      if (nextProps.interval !== this.props.interval) {
        clearInterval(this.intervalID);
        this.intervalID = setInterval(
          () => this.get(nextProps.interval),
          AUTO_REFRESH_INTERVAL,
        );
      }
    }
  }

  componentWillUnmount() {
    clearInterval(this.intervalID);
    this.intervalID = undefined;
  }

  render() {
    const autoRefreshStyle = this.state.autoRefresh
                           ? { backgroundColor: '#dde' }
                           : undefined;
    const props = this.props;
    return (
      <div style={styles.content}>
        <div style={styles.item}>
          <RaisedButton
            style={styles.time}
            icon={<Back />}
            disabled={props.back === undefined}
            onClick={() => this.context.router.push(this.props.back)}
          />
          <span style={styles.interval}>Latest:</span>
          <RaisedButton
            style={styles.time}
            labelStyle={styles.timeLabel}
            label="10 min"
            disabled={props.disableInterval || props.interval === 10 * minute}
            onClick={this.handleMinute}
          />
          <RaisedButton
            style={styles.time}
            labelStyle={styles.timeLabel}
            label="1 hour"
            disabled={props.disableInterval || props.interval === hour}
            onClick={this.handleHour}
          />
          <RaisedButton
            style={styles.time}
            labelStyle={styles.timeLabel}
            label="1 day"
            disabled={props.disableInterval || props.interval === day}
            onClick={this.handleDay}
          />
          <RaisedButton
            style={styles.time}
            labelStyle={styles.timeLabel}
            label="1 week"
            disabled={props.disableInterval || props.interval === week}
            onClick={this.handleWeek}
          />
        </div>
        <div style={styles.item}>
          from:&nbsp;
          <span style={styles.timestamp}>
            {/* {formatHeaderDate(this.props.from)} */}
            2017-08-23 12:34:30
          </span>
          &nbsp;
          to:&nbsp;
          <span style={styles.timestamp}>
            {/* {formatHeaderDate(this.props.to)} */}
            2017-08-23 12:34:30
          </span>
        </div>
        <RaisedButton
          label="Auto Refresh"
          labelStyle={styles.label}
          icon={<AutorefreshIcon style={styles.icon} />}
          onClick={this.handleAutoRefresh}
          buttonStyle={autoRefreshStyle}
          disabled={!this.props.autoRefresh}
        />
      </div>
    );
  }
}


export default Header;
