import React from 'react';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class Alerts extends React.Component {
  static propTypes = {
    style: React.PropTypes.object,
  }

  render() {
    const style = {
      ...styles.content,
      ...this.props.style,
    };
    return (
      <HoverPaper style={style}>
        <h3>Alerts</h3>
        <span style={styles.stat}>3 Alerts to show</span>
      </HoverPaper>
    );
  }
}


export default Alerts;
