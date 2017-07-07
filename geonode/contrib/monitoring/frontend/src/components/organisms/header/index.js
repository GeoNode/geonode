import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import RaisedButton from 'material-ui/RaisedButton';
import AutorefreshIcon from 'material-ui/svg-icons/action/autorenew';
import Back from 'material-ui/svg-icons/image/navigate-before';
import actions from './actions';
import styles from './styles';
import { minute, hour, day, week } from './constants';


const mapStateToProps = (state) => ({
  interval: state.interval.interval,
});


@connect(mapStateToProps, actions)
class Header extends React.Component {
  static contextTypes = {
    router: PropTypes.object.isRequired,
  }

  static propTypes = {
    interval: PropTypes.number,
    set: PropTypes.func.isRequired,
  }

  constructor(props) {
    super(props);
    this.handleBack = () => {
      this.context.router.goBack();
    };

    this.handleMinute = () => {
      this.props.set(10 * minute);
    };

    this.handleHour = () => {
      this.props.set(hour);
    };

    this.handleDay = () => {
      this.props.set(day);
    };

    this.handleWeek = () => {
      this.props.set(week);
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
          from:&nbsp;<span style={styles.timestamp}>05/29/2017 12:05:00</span>&nbsp;
          to:&nbsp;<span style={styles.timestamp}>05/29/2017 12:15:00</span>
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
