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
import styles from './styles';


const mapStateToProps = (state) => ({
  alertList: state.alertList.response,
  errorList: state.errorList.response,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps)
class HealthCheck extends React.Component {
  static propTypes = {
    alertList: PropTypes.object,
    errorList: PropTypes.object,
    style: PropTypes.object,
    timestamp: PropTypes.instanceOf(Date),
  }

  render() {
    const alertList = this.props.alertList;
    const alertNumber = alertList && alertList.data
                      ? alertList.data.problems.length
                      : 0;
    const alertStyle = alertNumber > 0
                     ? { backgroundColor: '#ffa031', color: '#fff' }
                     : {};
    const errorNumber = this.props.errorList
                      ? this.props.errorList.exceptions.length
                      : 0;
    const errorStyle = errorNumber > 0
                     ? { backgroundColor: '#d12b2b', color: '#fff' }
                     : {};
    const style = {
      ...styles.content,
      ...this.props.style,
      ...alertStyle,
      ...errorStyle,
    };
    return (
      <HoverPaper style={style}>
        <h3>Health Check</h3>
        <div style={styles.stat}>
          {alertNumber} alerts<br />
          {errorNumber} errors
        </div>
      </HoverPaper>
    );
  }
}


export default HealthCheck;
