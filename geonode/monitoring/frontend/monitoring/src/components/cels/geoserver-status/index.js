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
import SelectField from 'material-ui/SelectField';
import MenuItem from 'material-ui/MenuItem';
import AverageCPU from '../../molecules/average-cpu';
import AverageMemory from '../../molecules/average-memory';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  cpu: state.geoserverCpuStatus.response,
  mem: state.geoserverMemStatus.response,
  interval: state.interval.interval,
  timestamp: state.interval.timestamp,
  services: state.services.hostgeoserver,
});


@connect(mapStateToProps, actions)
class GeoserverStatus extends React.Component {
  static propTypes = {
    cpu: PropTypes.object,
    getCpu: PropTypes.func.isRequired,
    getMem: PropTypes.func.isRequired,
    interval: PropTypes.number,
    mem: PropTypes.object,
    resetCpu: PropTypes.func.isRequired,
    resetMem: PropTypes.func.isRequired,
    services: PropTypes.array,
    timestamp: PropTypes.instanceOf(Date),
  }

  constructor(props) {
    super(props);

    this.state = {
      host: '',
    };

    this.get = (
      host = this.state.host,
      interval = this.props.interval,
    ) => {
      this.props.getCpu(host, interval);
      this.props.getMem(host, interval);
    };

    this.handleChange = (event, target, host) => {
      this.setState({ host });
      this.get();
    };
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps && nextProps.services && nextProps.timestamp) {
      let host = nextProps.services[0].name;
      let firstTime = false;
      if (this.state.host === '') {
        firstTime = true;
        this.setState({ host });
      } else {
        host = this.state.host;
      }
      if (firstTime || nextProps.timestamp !== this.props.timestamp) {
        this.get(host, nextProps.interval);
      }
    }
  }

  componentWillUnmount() {
    this.props.resetCpu();
    this.props.resetMem();
  }

  render() {
    let cpu = 0;
    if (this.props.cpu) {
      cpu = undefined;
      const data = this.props.cpu.data.data;
      if (data.length > 0) {
        if (data[0].data.length > 0) {
          const metric = data[0].data[0];
          cpu = Math.floor(metric.val);
        }
      }
    }
    let mem = 0;
    if (this.props.mem) {
      mem = undefined;
      const data = this.props.mem.data.data;
      if (data.length > 0) {
        if (data[0].data.length > 0) {
          const metric = data[0].data[0];
          mem = Math.floor(metric.val);
        }
      }
    }
    const hosts = this.props.services
                ? this.props.services.map((host) =>
                  <MenuItem
                    key={host.name}
                    value={host.name}
                    primaryText={ `${host.name} [${host.host}]` }
                  />
                )
                : undefined;
    return this.props.services ? (
      <div style={styles.content}>
        <h5>GeoServer HW Status</h5>
        <SelectField
          floatingLabelText="Host"
          value={this.state.host}
          onChange={this.handleChange}
        >
          {hosts}
        </SelectField>
        <div style={styles.geonode}>
          <AverageCPU cpu={cpu} />
          <AverageMemory mem={mem} />
        </div>
      </div>
    ) : null;
  }
}


export default GeoserverStatus;
