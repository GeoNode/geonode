import React from 'react';
import PropTypes from 'prop-types';
import Header from '../../components/organisms/header';
import ErrorDetails from '../../components/organisms/error-detail';
import styles from './styles';


class Error extends React.Component {
  static propTypes = {
    params: PropTypes.object.isRequired,
  }

  render() {
    return (
      <div style={styles.root}>
        <Header disableInterval back="/errors" autoRefresh={false} />
        <ErrorDetails errorId={Number(this.props.params.errorId)} />
      </div>
    );
  }
}


export default Error;
