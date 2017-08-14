import React from 'react';
import HoverPaper from '../../atoms/hover-paper';
import HR from '../../atoms/hr';
import ResponseTable from '../../cels/response-table';
import styles from './styles';


class GeonodeLayerAnalytics extends React.Component {
  render() {
    return (
      <HoverPaper style={styles.content}>
        <h3>Geonode Layers Analytics</h3>
        <HR />
        <ResponseTable />
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
