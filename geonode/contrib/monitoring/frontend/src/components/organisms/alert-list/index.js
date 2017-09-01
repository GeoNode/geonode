import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import RaisedButton from 'material-ui/RaisedButton';
import CircularProgress from 'material-ui/CircularProgress';
import SettingsIcon from 'material-ui/svg-icons/action/settings';
import HoverPaper from '../../atoms/hover-paper';
import Alert from '../../cels/alert';
import actions from './actions';
import styles from './styles';


const mapStateToProps = (state) => ({
  alerts: state.alertList.response,
  interval: state.interval.interval,
  status: state.alertList.status,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps, actions)
class AlertList extends React.Component {
  static contextTypes = {
    router: PropTypes.object.isRequired,
  }

  static propTypes = {
    alerts: PropTypes.object,
    get: PropTypes.func.isRequired,
    interval: PropTypes.number,
    status: PropTypes.string,
    timestamp: PropTypes.instanceOf(Date),
  }

  constructor(props) {
    super(props);

    this.handleClick = () => {
      this.context.router.push('/alerts/settings');
    };

    this.get = (interval = this.props.interval) => {
      this.props.get(interval);
    };
  }

  componentWillMount() {
    this.get();
  }

  render() {
    const rawAlerts = this.props.alerts;
    let alerts;
    if (this.props.status === 'pending') {
      alerts = (
        <div style={styles.spinner}>
          <CircularProgress size={80} />
        </div>
      );
    } else {
      alerts = rawAlerts && rawAlerts.data && rawAlerts.data.problems.length > 0
             ? rawAlerts.data.problems.map((alert, index) => (
               <Alert
                 key={index}
                 alert={alert}
               />
             ))
             : [];
    }
    return (
      <HoverPaper style={styles.content}>
        <div style={styles.header}>
          <h3>Alerts</h3>
          <RaisedButton
            onClick={this.handleClick}
            style={styles.icon}
            icon={<SettingsIcon />}
          />
        </div>
        {alerts}
      </HoverPaper>
    );
  }
}


export default AlertList;
