import React, { Component } from 'react';
import PropTypes from 'prop-types';
import Snackbar from 'material-ui/Snackbar';
import reset from '../../reset.js';
import fonts from '../../fonts/fonts.js';
import { connect } from 'react-redux';
import actions from './actions';
import { Style } from 'radium';

const mapStateToProps = (state) => ({
  notifications: state.notifications.notifications,
  notificationsOpen: state.notifications.open,
  socketUrl: state.backend.socketUrl,
});


class App extends Component {
  componentWillMount() {
    // eslint-disable-next-line no-undef
    const hostname = window.location.hostname;
    this.props.setBackendUrl(hostname);
  }

  handleNotificationClose() {
    this.props.close();
  }

  render() {
    return (
      <div>
        <Style rules={fonts} />
        <Style rules={reset} />
        {this.props.children}
        <Snackbar
          open={this.props.notificationsOpen}
          message={this.props.notifications}
          autoHideDuration={5000}
          action="close"
          onActionTouchTap={this.handleNotificationClose}
          onRequestClose={this.handleNotificationClose}
        />
      </div>
    );
  }
}


App.propTypes = {
  children: PropTypes.node,
  notifications: PropTypes.node,
  notificationsOpen: PropTypes.bool,
  close: PropTypes.func.isRequired,
  setBackendUrl: PropTypes.func.isRequired,
};

App.childContextTypes = {
  socket: PropTypes.object,
};


export default connect(mapStateToProps, actions)(App);
