import React from 'react';
import HoverPaper from '../../atoms/hover-paper';
import styles from './styles';


class Errors extends React.Component {
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
        <h3>Errors</h3>
        <span style={styles.stat}>3 Errors occured</span>
      </HoverPaper>
    );
  }
}


Errors.propTypes = {
  style: React.PropTypes.object,
};


export default Errors;
