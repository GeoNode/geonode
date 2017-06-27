import React from 'react';
import PropTypes from 'prop-types';
import RaisedButton from 'material-ui/RaisedButton';
import AutorefreshIcon from 'material-ui/svg-icons/action/autorenew';
import Back from 'material-ui/svg-icons/image/navigate-before';
import styles from './styles';


class Header extends React.Component {
  static contextTypes = {
    router: PropTypes.object.isRequired,
  }

  constructor(props) {
    super(props);
    this.handleBack = () => {
      this.context.router.goBack();
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
            disabled
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
