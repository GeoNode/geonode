import React from 'react';
import PropTypes from 'prop-types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import styles from './styles';


class ResponseTime extends React.Component {
  static propTypes = {
    average: PropTypes.number.isRequired,
    data: PropTypes.array.isRequired,
    from: PropTypes.object,
    last: PropTypes.number.isRequired,
    max: PropTypes.number.isRequired,
    to: PropTypes.object,
  }

  render() {
    return (
      <div style={styles.content}>
        <h4>Response Time</h4>
        Last Response Time: {this.props.last} ms<br />
        Max Response Time: {this.props.max} ms<br />
        Average Response Time: {this.props.average} ms<br />
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
          <Line type="monotone" dataKey="time" stroke="#8884d8" activeDot={{ r: 8 }} />
        </LineChart>
      </div>
    );
  }
}


export default ResponseTime;
