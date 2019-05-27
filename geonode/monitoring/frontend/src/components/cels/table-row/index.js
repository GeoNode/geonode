import React from 'react';
import PropTypes from 'prop-types';
import { TableRow } from 'material-ui/Table';
import styles from './styles';


class MyTableRow extends React.Component {
  static propTypes = {
    children: PropTypes.node,
  }
  render() {
    return (
      <TableRow>{this.props.children}</TableRow>
    );
  }
}


export default MyTableRow;
