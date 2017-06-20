import React from 'react';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class AverageCPU extends React.Component {
  static propTypes = {
    cpu: React.PropTypes.number.isRequired,
  }

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


export default AverageCPU;
