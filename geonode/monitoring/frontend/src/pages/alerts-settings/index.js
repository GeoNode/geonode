import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import Header from '../../components/organisms/header';
import AlertSetting from '../../components/organisms/alert-setting';
import HoverPaper from '../../components/atoms/hover-paper';
import actions from './actions';
import styles from './styles';


const mapStateToProps = (state) => ({
  alerts: state.alertSettings.response,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps, actions)
class AlertsSettings extends React.Component {
  static propTypes = {
    alerts: PropTypes.object,
    get: PropTypes.func.isRequired,
    timestamp: PropTypes.instanceOf(Date),
  }

  constructor(props) {
    super(props);

    this.get = () => {
      this.props.get();
    };
  }

  componentWillMount() {
    this.get();
  }

  render() {
    const { alerts } = this.props;
    let alertList = [];
    if (alerts) {
      alertList = alerts.data;
    }
    return (
      <div style={styles.root}>
        <Header back="/alerts" disableInterval autoRefresh={false} />
        <HoverPaper style={styles.content}>
          <div style={styles.header}>
            <h3>Alerts Settings</h3>
          </div>
          {
            alertList.map((alert, index) => (
              <AlertSetting alert={alert} key={index} autoFocus={index === 0} />
            ))
          }
        </HoverPaper>
      </div>
    );
  }
}


export default AlertsSettings;
