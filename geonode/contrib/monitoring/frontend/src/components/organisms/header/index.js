import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import RaisedButton from 'material-ui/RaisedButton';
import AutorefreshIcon from 'material-ui/svg-icons/action/autorenew';
import Back from 'material-ui/svg-icons/image/navigate-before';
import { formatHeaderDate } from '../../../utils';
import { minute, hour, day, week } from '../../../constants';
import actions from './actions';
import styles from './styles';
import { AUTO_REFRESH_INTERVAL } from './constants';


const mapStateToProps = (state) => ({
  from: state.interval.from,
  interval: state.interval.interval,
  to: state.interval.to,
});


@connect(mapStateToProps, actions)
class Header extends React.Component {
  static contextTypes = {
    router: PropTypes.object.isRequired,
  }

  static propTypes = {
    interval: PropTypes.number,
    setInterval: PropTypes.func.isRequired,
    from: PropTypes.object,
    to: PropTypes.object,
  }

  constructor(props) {
    super(props);

    this.state = {
      autoRefresh: false,
    };

    this.get = (interval = this.props.interval) => {
      const now = new Date();
      const seconds = Math.floor(now.getSeconds() / 10) * 10;
      now.setSeconds(seconds, 0);
      const fromDate = new Date(now - interval * 1000);
      this.props.setInterval(fromDate, now, interval);
    };

    this.handleBack = () => {
      this.context.router.push('/');
    };

    this.handleMinute = () => {
      const now = new Date();
      now.setSeconds(0, 0);
      const interval = 10 * minute;
      const fromDate = new Date(now - interval * 1000);
      this.props.setInterval(fromDate, now, interval);
    };

    this.handleHour = () => {
      const now = new Date();
      now.setSeconds(0, 0);
      const fromDate = new Date(now - hour * 1000);
      this.props.setInterval(fromDate, now, hour);
    };

    this.handleDay = () => {
      const now = new Date();
      now.setSeconds(0, 0);
      const fromDate = new Date(now - day * 1000);
      this.props.setInterval(fromDate, now, day);
    };

    this.handleWeek = () => {
      const now = new Date();
      now.setSeconds(0, 0);
      const fromDate = new Date(now - week * 1000);
      this.props.setInterval(fromDate, now, week);
    };

    this.handleAutoRefresh = () => {
      if (this.state.autoRefresh) {
        clearInterval(this.intervalID);
        this.intervalID = undefined;
        this.setState({ autoRefresh: false });
      } else {
        this.intervalID = setInterval(this.get, AUTO_REFRESH_INTERVAL);
        this.setState({ autoRefresh: true });
        this.get();
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
    return (
      <div style={styles.content}>
        <div style={styles.item}>
          <RaisedButton
            style={styles.time}
            icon={<Back />}
            onClick={this.handleBack}
          />
          <span style={styles.interval}>Latest:</span>
          <RaisedButton
            style={styles.time}
            labelStyle={styles.timeLabel}
            label="10 min"
            disabled={this.props.interval === 10 * minute}
            onClick={this.handleMinute}
          />
          <RaisedButton
            style={styles.time}
            labelStyle={styles.timeLabel}
            label="1 hour"
            disabled={this.props.interval === hour}
            onClick={this.handleHour}
          />
          <RaisedButton
            style={styles.time}
            labelStyle={styles.timeLabel}
            label="1 day"
            disabled={this.props.interval === day}
            onClick={this.handleDay}
          />
          <RaisedButton
            style={styles.time}
            labelStyle={styles.timeLabel}
            label="1 week"
            disabled={this.props.interval === week}
            onClick={this.handleWeek}
          />
        </div>
        <div style={styles.item}>
          from:&nbsp;
          <span style={styles.timestamp}>
            {formatHeaderDate(this.props.from)}
          </span>
          &nbsp;
          to:&nbsp;
          <span style={styles.timestamp}>
            {formatHeaderDate(this.props.to)}
          </span>
        </div>
        <RaisedButton
          label="Auto Refresh"
          labelStyle={styles.label}
          icon={<AutorefreshIcon style={styles.icon} />}
          onClick={this.handleAutoRefresh}
          buttonStyle={autoRefreshStyle}
        />
      </div>
    );
  }
}


export default Header;
