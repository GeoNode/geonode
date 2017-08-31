import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import RaisedButton from 'material-ui/RaisedButton';
import SettingsIcon from 'material-ui/svg-icons/action/settings';
import HoverPaper from '../../atoms/hover-paper';
import Alert from '../../cels/alert';
import actions from './actions';
import styles from './styles';


const mapStateToProps = (state) => ({
  alerts: state.alertList.response,
  interval: state.interval.interval,
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
    const alerts = this.props.alerts && this.props.alerts.data.length > 0
                 ? this.props.alerts.data[0].problems
                 : [];
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
        {
          alerts.map((alert, index) => (
            <Alert
              key={index}
              short={alert.message}
              offending={alert.offending_value}
              threshold={alert.threshold_value}
            />
          ))
        }
      </HoverPaper>
    );
  }
}


export default AlertList;
