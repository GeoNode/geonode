import React from 'react';
import PropTypes from 'prop-types';
import RaisedButton from 'material-ui/RaisedButton';
import SettingsIcon from 'material-ui/svg-icons/action/settings';
import HoverPaper from '../../atoms/hover-paper';
import Alert from '../../cels/alert';
import styles from './styles';


class AlertList extends React.Component {
  static contextTypes = {
    router: PropTypes.object.isRequired,
  }

  constructor(props) {
    super(props);

    this.handleClick = () => {
      this.context.router.push('/alerts/settings');
    };
  }

  render() {
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
        <Alert
          date="05/29/2017 12:11:01"
          short="Geonode was not responding"
        />
        <Alert
          date="05/29/2017 12:07:32"
          short="Geonode served more than 10MB/m"
        />
      </HoverPaper>
    );
  }
}


export default AlertList;
