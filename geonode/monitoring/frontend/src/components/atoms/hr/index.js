import React from 'react';
import PropTypes from 'prop-types';
import styles from './styles';


class HR extends React.Component {
  static propTypes = {
    children: PropTypes.node,
    style: PropTypes.object,
  }

  render() {
    return (
      <hr style={styles.hr} />
    );
  }
}


export default HR;
