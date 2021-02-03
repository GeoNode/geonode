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
import HoverPaper from '../../atoms/hover-paper';
import Map from '../../atoms/map';
import styles from './styles';


class MostActiveIPs extends React.Component {
  render() {
    return (
      <HoverPaper style={styles.content}>
        <h3>Most Active IPs</h3>
        <div style={styles.map}>
          <Map />
        </div>
      </HoverPaper>
    );
  }
}


export default MostActiveIPs;
