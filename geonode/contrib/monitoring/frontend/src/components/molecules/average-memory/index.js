import React, { Component } from 'react';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class AverageMemory extends Component {
  render() {
    return (
      <HoverPaper style={styles.content}>
        <h5>Average Memory</h5>
        <div style={styles.stat}>
          <h3>{this.props.memory}%</h3>
        </div>
      </HoverPaper>
    );
  }
}


AverageMemory.propTypes = {
  memory: React.PropTypes.number.isRequired,
};


export default AverageMemory;
