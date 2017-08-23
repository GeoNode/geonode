import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { getResponseData, getErrorCount } from '../../../utils';
import HoverPaper from '../../atoms/hover-paper';
import HR from '../../atoms/hr';
import ResponseTable from '../../cels/response-table';
import styles from './styles';
import actions from './actions';


const mapStateToProps = (state) => ({
  interval: state.interval.interval,
  response: state.geonodeLayerResponse.response,
  errorNumber: state.geonodeLayerError.response,
});


@connect(mapStateToProps, actions)
class GeonodeLayerAnalytics extends React.Component {
  static propTypes = {
    getResponses: PropTypes.func.isRequired,
    resetResponses: PropTypes.func.isRequired,
    getErrors: PropTypes.func.isRequired,
    resetErrors: PropTypes.func.isRequired,
    interval: PropTypes.number,
    response: PropTypes.object,
    errorNumber: PropTypes.object,
    timestamp: PropTypes.instanceOf(Date),
  }

  constructor(props) {
    super(props);
    this.get = (interval = this.props.interval) => {
      this.props.getErrors(interval);
      this.props.getResponses(interval);
    };

    this.reset = () => {
      this.props.resetErrors();
      this.props.resetResponses();
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

  componentWillUnmount() {
    this.reset();
  }

  render() {
    let average = 0;
    let max = 0;
    let requests = 0;
    [
      average,
      max,
      requests,
    ] = getResponseData(this.props.response);
    const errorNumber = getErrorCount(this.props.errorNumber);
    return (
      <HoverPaper style={styles.content}>
        <h3>Geonode Layers Analytics</h3>
        <HR />
        <ResponseTable
          average={average}
          max={max}
          requests={requests}
          errorNumber={errorNumber}
        />
        <table style={styles.table}>
          <thead>
            <tr>
              <th>
                Most Frequently Accessed Layers
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row"></th>
              <td>Layer Name</td>
              <td>Count</td>
            </tr>
            <tr>
              <th scope="row">1</th>
              <td>geonode:layer</td>
              <td>###</td>
            </tr>
            <tr>
              <th scope="row">2</th>
              <td>geonode:layer</td>
              <td>###</td>
            </tr>
            <tr>
              <th scope="row">3</th>
              <td>geonode:layer</td>
              <td>###</td>
            </tr>
          </tbody>
        </table>
      </HoverPaper>
    );
  }
}


export default GeonodeLayerAnalytics;
