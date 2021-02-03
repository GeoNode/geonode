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
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  interval: state.interval.interval,
  layers: state.frequentLayers.response,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps, actions)
class Alert extends React.Component {
  static propTypes = {
    get: PropTypes.func.isRequired,
    interval: PropTypes.number,
    layers: PropTypes.object,
    timestamp: PropTypes.instanceOf(Date),
  };

  static defaultProps = {
    layers: {
      data: {
        data: [{
          data: [],
        }],
      },
    },
  }

  constructor(props) {
    super(props);

    this.get = (interval = this.props.interval) => {
      this.props.get(interval);
    };
  }

  componentWillMount() {
    this.get();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps) {
      if (nextProps.timestamp && nextProps.timestamp !== this.props.timestamp) {
        this.get(nextProps.interval);
      }
    }
  }

  render() {
    const layersData = this.props.layers.data.data[0].data;
    const layers = layersData.map((layer, index) => (
        <tr key={layer.resource.name}>
          <th scope="row">{index + 1}</th>
          <td>{layer.resource.name}</td>
          <td>{Number(layer.val)}</td>
        </tr>
    ));
    return (
      <div style={styles.root}>
        <h5 style={styles.title}>Most Frequently Accessed Layers</h5>
        <table style={styles.table}>
          <tbody>
            <tr>
              <th scope="row"></th>
              <td>Layer Name</td>
              <td>Requests</td>
            </tr>
            {layers}
          </tbody>
        </table>
      </div>
    );
  }
}


export default Alert;
