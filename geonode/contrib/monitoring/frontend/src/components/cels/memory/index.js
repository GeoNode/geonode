import React from 'react';
import PropTypes from 'prop-types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import styles from './styles';


class Memory extends React.Component {
  static propTypes = {
    data: PropTypes.array.isRequired,
  }

  render() {
    return (
      <div style={styles.content}>
        <h4>Memory</h4>
        <LineChart
          width={500}
          height={300}
          data={this.props.data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <XAxis dataKey="name" />
          <YAxis unit="%" />
          <CartesianGrid strokeDasharray="3 3" />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="MEM used"
            stroke="#8884d8"
          />
        </LineChart>
      </div>
    );
  }
}


export default Memory;
