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
import {
  Table,
  TableBody,
  TableHeader,
  TableHeaderColumn,
  TableRow,
  TableRowColumn,
} from 'material-ui/Table';
import styles from './styles';
import actions from './actions';
import {withRouter} from 'react-router-dom';

const mapStateToProps = (state) => ({
  errorList: state.errorList.response,
  interval: state.interval.interval,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps, actions)
class ErrorList extends React.Component {

  static propTypes = {
    errorList: PropTypes.object,
    get: PropTypes.func.isRequired,
    interval: PropTypes.number,
    timestamp: PropTypes.instanceOf(Date),
  }

  constructor(props) {
    super(props);

    this.handleClick = (row, column, event) => {
      this.props.history.push(`/errors/${event.target.dataset.id}`);
    };
  }

  componentWillMount() {
    this.props.get(this.props.interval);
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps && nextProps.interval) {
      if (this.props.timestamp !== nextProps.timestamp) {
        this.props.get(nextProps.interval);
      }
    }
  }

  render() {
    const errorList = this.props.errorList;
    const errors = this.props.errorList
                 ? errorList.exceptions.map(
                   error => <TableRow key={error.id}>
                     <TableRowColumn data-id={error.id}>{error.id}</TableRowColumn>
                     <TableRowColumn data-id={error.id}>{error.error_type}</TableRowColumn>
                     <TableRowColumn data-id={error.id}>{error.service.name}</TableRowColumn>
                     <TableRowColumn data-id={error.id}>{error.created}</TableRowColumn>
                   </TableRow>
                 ) : '';
    return (
      <HoverPaper style={styles.content}>
        <div style={styles.header}>
          <h3 style={styles.title}>Errors</h3>
        </div>
        <Table onCellClick={this.handleClick}>
          <TableHeader displaySelectAll={false}>
            <TableRow>
              <TableHeaderColumn>ID</TableHeaderColumn>
              <TableHeaderColumn>Type</TableHeaderColumn>
              <TableHeaderColumn>Service</TableHeaderColumn>
              <TableHeaderColumn>Date</TableHeaderColumn>
            </TableRow>
          </TableHeader>
          <TableBody showRowHover stripedRows displayRowCheckbox={false}>
            {errors}
          </TableBody>
        </Table>
      </HoverPaper>
    );
  }
}


export default withRouter(ErrorList);
