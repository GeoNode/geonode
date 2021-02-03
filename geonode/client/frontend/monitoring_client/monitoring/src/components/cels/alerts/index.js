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
import HoverPaper from '../../atoms/hover-paper';
import actions from '../../organisms/alert-list/actions';
import styles from './styles';
import {withRouter} from 'react-router-dom';

const mapStateToProps = (state) => ({
  alertList: state.alertList.response,
  interval: state.interval.interval,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps, actions)
class Alerts extends React.Component {
  static propTypes = {
    alertList: PropTypes.object,
    get: PropTypes.func.isRequired,
    interval: PropTypes.number,
    style: PropTypes.object,
    timestamp: PropTypes.instanceOf(Date),
  }

  constructor(props) {
    super(props);

    this.handleClick = () => {
      this.props.history.push('/alerts');
    };

    this.get = (interval = this.props.interval) => {
      this.props.get(interval);
    };
  }

  componentWillMount() {
    this.get();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps) {
      if (nextProps.timestamp && nextProps.timestamp !== this.props.timestamp) {
        this.get(nextProps.interval);
      }
    }
  }

  render() {
    const alertList = this.props.alertList;
    const alertNumber = alertList && alertList.data
                      ? alertList.data.problems.length
                      : 0;
    const extraStyle = alertNumber > 0
                     ? { backgroundColor: '#ffa031', color: '#fff' }
                     : {};
    const style = {
      ...styles.content,
      ...this.props.style,
      ...extraStyle,
    };
    return (
      <HoverPaper style={style}>
        <div onClick={this.handleClick} style={styles.clickable}>
          <h3>Alerts</h3>
          <span style={styles.stat}>{alertNumber} Alerts to show</span>
        </div>
      </HoverPaper>
    );
  }
}


export default withRouter(Alerts);
