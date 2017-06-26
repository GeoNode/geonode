import React from 'react';
import styles from './styles';


class HR extends React.Component {
  static propTypes = {
    children: React.PropTypes.node,
    style: React.PropTypes.object,
  }

  render() {
    return (
      <hr style={styles.hr} />
    );
  }
}


export default HR;
