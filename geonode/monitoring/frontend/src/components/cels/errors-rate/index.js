import React from 'react';
import PropTypes from 'prop-types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import styles from './styles';


class ErrorsRate extends React.Component {
  static propTypes = {
    data: PropTypes.array.isRequired,
  }

  render() {
    let totalCount = 0;
    if (this.props.data.length > 0) {
      totalCount = this.props.data.reduce(
        (previous, current) => (current.count + previous),
        0,
      );
    }
    return (
      <div style={styles.content}>
        <h4>Errors Rate</h4>
        Total Count: {totalCount}
        <LineChart
          width={500}
          height={300}
          data={this.props.data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <XAxis dataKey="name" />
          <YAxis />
          <CartesianGrid strokeDasharray="3 3" />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="count" stroke="#82ca9d" />
        </LineChart>
      </div>
    );
  }
}


export default ErrorsRate;
