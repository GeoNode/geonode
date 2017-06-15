import React, { Component } from 'react';
import RaisedButton from 'material-ui/RaisedButton';
import AutorefreshIcon from 'material-ui/svg-icons/action/autorenew';
import styles from './styles';


class Header extends Component {
  render() {
    return (
      <div style={styles.content}>
        <div style={styles.item}>
          <span style={styles.interval}>Latest:</span>
          <RaisedButton
            style={styles.time}
            labelStyle={styles.timeLabel}
            label="10 min"
          />
          <RaisedButton
            style={styles.time}
            labelStyle={styles.timeLabel}
            label="1 hour"
          />
          <RaisedButton
            style={styles.time}
            labelStyle={styles.timeLabel}
            label="1 day"
          />
          <RaisedButton
            style={styles.time}
            labelStyle={styles.timeLabel}
            label="1 week"
          />
        </div>
        <div style={styles.item}>
          from: <span style={styles.timestamp}>05/29/2017 12:05:00</span>
          to: <span style={styles.timestamp}>05/29/2017 12:15:00</span>
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
