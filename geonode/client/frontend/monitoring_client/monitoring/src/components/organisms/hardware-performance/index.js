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
import RaisedButton from 'material-ui/RaisedButton';
import ChartIcon from 'material-ui/svg-icons/av/equalizer';
import HoverPaper from '../../atoms/hover-paper';
import GeonodeStatus from '../../cels/geonode-status';
import GeoserverStatus from '../../cels/geoserver-status';
import styles from './styles';
import {withRouter} from 'react-router-dom';

class HardwarePerformance extends React.Component {
  constructor(props) {
    super(props);

    this.handleClick = () => {
      this.props.history.push('/performance/hardware');
    };
  }

  render() {
    return (
      <HoverPaper style={styles.content}>
        <div style={styles.header}>
          <h3 style={styles.title}>Hardware Performance</h3>
          <RaisedButton
            onClick={this.handleClick}
            style={styles.icon}
            icon={<ChartIcon />}
          />
        </div>
        <GeonodeStatus />
        <GeoserverStatus />
      </HoverPaper>
    );
  }
}


export default withRouter(HardwarePerformance);
