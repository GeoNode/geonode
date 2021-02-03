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
import GeonodeData from '../../cels/geonode-data';
import WSData from '../../cels/ws-data';
import styles from './styles';
import {withRouter} from 'react-router-dom';

class SoftwarePerformance extends React.Component {

  constructor(props) {
    super(props);

    this.handleClick = () => {
      this.props.history.push('/performance/software');
    };
  }

  render() {
    return (
      <HoverPaper style={styles.content}>
        <div style={styles.header}>
          <h3 style={styles.title}>Software Performance</h3>
          <RaisedButton
            onClick={this.handleClick}
            style={styles.icon}
            icon={<ChartIcon />}
          />
        </div>
        <GeonodeData />
        <WSData />
      </HoverPaper>
    );
  }
}


export default withRouter(SoftwarePerformance);
