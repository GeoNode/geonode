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


const mapStateToProps = (state) => ({
  errorList: state.errorList.response,
  interval: state.interval.interval,
  timestamp: state.interval.timestamp,
});


@connect(mapStateToProps, actions)
class ErrorList extends React.Component {
  static contextTypes = {
    router: PropTypes.object.isRequired,
  }

  static propTypes = {
    errorList: PropTypes.object,
    get: PropTypes.func.isRequired,
    interval: PropTypes.number,
    timestamp: PropTypes.instanceOf(Date),
  }

  constructor(props) {
    super(props);

    this.handleClick = (row, column, event) => {
      this.context.router.push(`/errors/${event.target.dataset.id}`);
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


export default ErrorList;
