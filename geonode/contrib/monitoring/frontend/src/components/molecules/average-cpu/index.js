import React, { Component } from 'react';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class AverageCPU extends Component {
  render() {
    return (
      <HoverPaper style={styles.content}>
        <h5>Average CPU</h5>
        <div style={styles.stat}>
          <h3>{this.props.cpu}%</h3>
        </div>
      </HoverPaper>
    );
  }
}


AverageCPU.propTypes = {
  cpu: React.PropTypes.number.isRequired,
};


export default AverageCPU;
