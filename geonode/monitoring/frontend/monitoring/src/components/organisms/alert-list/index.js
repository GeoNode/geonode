/*
#########################################################################
#
# Copyright (C) 2019 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
*/

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
import {withRouter} from 'react-router-dom';

const mapStateToProps = (state) => ({
  alerts: state.alertList.response,
  interval: state.interval.interval,
  status: state.alertList.status,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps, actions)
class AlertList extends React.Component {

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
      this.props.history.push('/alerts-settings');
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


export default withRouter(AlertList);
