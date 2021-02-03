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
import CPU from '../../cels/cpu';
import SelectField from 'material-ui/SelectField';
import MenuItem from 'material-ui/MenuItem';
import Memory from '../../cels/memory';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  cpu: state.geoserverCpuSequence.response,
  memory: state.geoserverMemorySequence.response,
  interval: state.interval.interval,
  services: state.services.hostgeoserver,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps, actions)
class GeoserverStatus extends React.Component {
  static propTypes = {
    cpu: PropTypes.object,
    getCpu: PropTypes.func.isRequired,
    getMemory: PropTypes.func.isRequired,
    memory: PropTypes.object,
    services: PropTypes.array,
    resetCpu: PropTypes.func.isRequired,
    resetMemory: PropTypes.func.isRequired,
    timestamp: PropTypes.instanceOf(Date),
    interval: PropTypes.number,
    half: PropTypes.bool,
  }

  static defaultProps = {
    half: true,
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
      this.props.getMemory(host, interval);
    };

    this.reset = () => {
      this.props.resetCpu();
      this.props.resetMemory();
    };
  }

  componentWillMount() {
    this.setHost(this.props);

  }

  componentWillReceiveProps(nextProps) {
    this.setHost(nextProps);
  }

  componentWillUnmount() {
    this.reset();
  }

  render() {
    let cpuData = [];
    let memoryData = [];
    if (
      this.props.cpu
      && this.props.cpu.data
      && this.props.cpu.data.data
    ) {
      cpuData = this.props.cpu.data.data.map(element => ({
        name: element.valid_from,
        'CPU used': element.data.length > 0 ? Math.floor(element.data[0].val) : 0,
      }));
    }
    if (
      this.props.memory
      && this.props.memory.data
      && this.props.memory.data.data
    ) {
      memoryData = this.props.memory.data.data.map(element => ({
        name: element.valid_from,
        'MEM used': element.data.length > 0 ? Math.floor(element.data[0].val) : 0,
      }));
    }
    const contentStyle = this.props.half
                       ? styles.content
                       : { ...styles.content, width: '100%' };
    const hosts = this.props.services
                ? this.props.services.map((host) =>
                  <MenuItem
                    key={host.name}
                    value={host.name}
                    primaryText={ `${host.name} [${host.host}]`}
                  />
                )
                : undefined;
    return (
      <HoverPaper style={contentStyle}>
        <h3>GeoServer status</h3>
        <SelectField
          floatingLabelText="Host"
          value={this.state.host}
          onChange={this.handleChange}
        >
          {hosts}
        </SelectField>
        <div style={styles.stat}>
          <CPU data={cpuData} />
          <Memory data={memoryData} />
        </div>
      </HoverPaper>
    );
  }

  setHost = (props) => {
    if (props && props.services && props.timestamp) {
      let host = props.services[0].name;
      let firstTime = false;
      if (this.state.host === '') {
        firstTime = true;
        this.setState({ host });
      } else {
        host = this.state.host;
      }
      if (firstTime || props.timestamp !== this.props.timestamp) {
        this.get(host, props.interval);
      }
    }
  }
}


export default GeoserverStatus;
