import React from 'react';
import RaisedButton from 'material-ui/RaisedButton';
import Header from '../../components/organisms/header';
import AlertSetting from '../../components/organisms/alert-setting';
import HoverPaper from '../../components/atoms/hover-paper';
import styles from './styles';


class AlertsSettings extends React.Component {
  render() {
    return (
      <div style={styles.root}>
        <Header back="/alerts" disableInterval autoRefresh={false} />
        <HoverPaper style={styles.content}>
          <div style={styles.header}>
            <h3>Alerts Settings</h3>
            <RaisedButton
              onClick={this.handleClick}
              style={styles.icon}
              label="save"
            />
          </div>
          <AlertSetting autoFocus />
          <AlertSetting />
        </HoverPaper>
      </div>
    );
  }
}


export default AlertsSettings;
