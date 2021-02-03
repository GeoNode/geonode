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
import HealthCheck from '../../cels/health-check';
import Uptime from '../../cels/uptime';
import Alerts from '../../cels/alerts';
import Errors from '../../cels/errors';
import styles from './styles';


class Stats extends React.Component {
  render() {
    return (
      <div style={styles.content}>
        <div style={styles.first}>
          <HealthCheck />
          <Uptime />
        </div>
        <div style={styles.second}>
          <Alerts />
          <Errors />
        </div>
      </div>
    );
  }
}


export default Stats;
