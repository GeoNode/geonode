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
import Header from '../../components/organisms/header';
import GeonodeStatus from '../../components/organisms/geonode-status';
import GeoserverStatus from '../../components/organisms/geoserver-status';
import styles from './styles';


const mapStateToProps = (state) => ({
  services: state.services.hostgeoserver,
});


@connect(mapStateToProps)
class HWPerf extends React.Component {
  static propTypes = {
    services: PropTypes.array,
  }

  render() {
    return (
      <div style={styles.root}>
        <Header back="/" />
        <div style={styles.analytics}>
          <GeonodeStatus />
          {
            this.props.services
            ? <GeoserverStatus />
            : false
          }
        </div>
      </div>
    );
  }
}


export default HWPerf;
