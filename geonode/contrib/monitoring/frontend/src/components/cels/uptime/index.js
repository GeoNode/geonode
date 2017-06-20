import React from 'react';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class Uptime extends React.Component {
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
        <h3>Uptime</h3>
        <span style={styles.stat}>10 days</span>
      </HoverPaper>
    );
  }
}


Uptime.propTypes = {
  style: React.PropTypes.object,
};


export default Uptime;
