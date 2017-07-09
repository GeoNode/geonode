import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import RaisedButton from 'material-ui/RaisedButton';
import AutorefreshIcon from 'material-ui/svg-icons/action/autorenew';
import Back from 'material-ui/svg-icons/image/navigate-before';
import actions from './actions';
import styles from './styles';
import { minute, hour, day, week } from './constants';
import formatDate from './utils';


const rightNow = new Date();


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
    set: PropTypes.func.isRequired,
    from: PropTypes.object,
    to: PropTypes.object,
  }

  static defaultProps = {
    from: rightNow,
    interval: 10 * minute,
    to: new Date(rightNow - 10 * minute * 1000),
  }


  constructor(props) {
    super(props);
    this.handleBack = () => {
      this.context.router.goBack();
    };

    this.handleMinute = () => {
      const now = new Date();
      const interval = 10 * minute;
      const fromDate = new Date(now - interval * 1000);
      this.props.set(now, fromDate, interval);
    };

    this.handleHour = () => {
      const now = new Date();
      const fromDate = new Date(now - hour);
      this.props.set(now, fromDate, hour);
    };

    this.handleDay = () => {
      const now = new Date();
      const fromDate = new Date(now - day);
      this.props.set(now, fromDate, day);
    };

    this.handleWeek = () => {
      const now = new Date();
      const fromDate = new Date(now - week);
      this.props.set(now, fromDate, week);
    };
  }

  render() {
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
          from:&nbsp;<span style={styles.timestamp}>{formatDate(this.props.from)}</span>&nbsp;
          to:&nbsp;<span style={styles.timestamp}>{formatDate(this.props.to)}</span>
        </div>
        <RaisedButton
          label="Auto Refresh"
          labelStyle={styles.label}
          icon={<AutorefreshIcon style={styles.icon} />}
        />
      </div>
    );
  }
}


export default Header;
