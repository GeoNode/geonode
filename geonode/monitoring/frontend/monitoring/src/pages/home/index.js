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
import HoverPaper from '../../components/atoms/hover-paper';
import Map from '../../components/atoms/map';
import Header from '../../components/organisms/header';
import Stats from '../../components/organisms/stats';
import SoftwarePerformance from '../../components/organisms/software-performance';
import HardwarePerformance from '../../components/organisms/hardware-performance';
import styles from './styles';


class Home extends React.Component {
  render() {
    return (
      <div style={styles.root}>
        <Header />
        <Stats />
        <div style={styles.content}>
          <SoftwarePerformance />
          <div style={styles.hardware}>
            <HardwarePerformance />
            <HoverPaper>
              <Map />
            </HoverPaper>
          </div>
        </div>
      </div>
    );
  }
}


export default Home;
