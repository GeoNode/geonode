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
import Header from '../../components/organisms/header';
import GeonodeAnalytics from '../../components/organisms/geonode-analytics';
import GeonodeLayersAnalytics from '../../components/organisms/geonode-layers-analytics';
import WSAnalytics from '../../components/organisms/ws-analytics';
import WSLayersAnalytics from '../../components/organisms/ws-layers-analytics';
import styles from './styles';


class SWPerf extends React.Component {
  render() {
    return (
      <div style={styles.root}>
        <Header back="/" />
        <div style={styles.analytics}>
          <GeonodeAnalytics />
          <WSAnalytics />
        </div>
        <div style={styles.analytics}>
          <GeonodeLayersAnalytics />
          <WSLayersAnalytics />
        </div>
      </div>
    );
  }
}


export default SWPerf;
