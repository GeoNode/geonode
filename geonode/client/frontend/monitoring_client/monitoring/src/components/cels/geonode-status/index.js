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
  cpu: state.geonodeCpuStatus.response,
  interval: state.interval.interval,
  mem: state.geonodeMemStatus.response,
  services: state.services.hostgeonode,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps, actions)
class GeonodeStatus extends React.Component {
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
          const value = Number(metric.val);
          if (value > 1) {
            cpu = Math.floor(value);
          } else {
            cpu = Number(value.toFixed(2));
          }
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
          const value = Number(metric.val);
          if (value > 1) {
            mem = Math.floor(value);
          } else {
            mem = Number(value.toFixed(2));
          }
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
    return (
      <div style={styles.content}>
        <SelectField
          floatingLabelText="Host"
          value={this.state.host}
          onChange={this.handleChange}
        >
          {hosts}
        </SelectField>
        <h5>GeoNode HW Status</h5>
        <div style={styles.geonode}>
          <AverageCPU cpu={cpu} />
          <AverageMemory mem={mem} />
        </div>
      </div>
    );
  }
}


export default GeonodeStatus;
