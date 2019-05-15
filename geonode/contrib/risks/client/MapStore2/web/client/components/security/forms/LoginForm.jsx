/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {FormControl, FormGroup, ControlLabel, Button, Alert} = require('react-bootstrap');
const Spinner = require('react-spinkit');
const Message = require('../../../components/I18N/Message');
const LocaleUtils = require('../../../utils/LocaleUtils');

  /**
   * A Form to login menu for user details:
   */
const LoginForm = React.createClass({
    propTypes: {
      // props
      user: React.PropTypes.object,
      onLoginSuccess: React.PropTypes.func,
      showSubmitButton: React.PropTypes.bool,
      loginError: React.PropTypes.object,

      // actions
      onSubmit: React.PropTypes.func,
      onError: React.PropTypes.func,

      // localization
      userNameText: React.PropTypes.node,
      passwordText: React.PropTypes.node,
      loginFailedStatusMessages: React.PropTypes.object,
      loginFailedMessage: React.PropTypes.node
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
          onSubmit: () => {},
          onLoginError: () => {},
          showSubmitButton: true,
          userNameText: <Message msgId="user.username"/>,
          passwordText: <Message msgId="user.password"/>,
          loginFailedMessage: <Message msgId="user.loginFail"/>,
          loginFailedStatusMessages: {
              0: <Message msgId="user.loginFailedStatusMessages.usernamePwdInsert"/>,
              401: <Message msgId="user.loginFailedStatusMessages.usernamePwdIncorrect"/>
          }

      };
    },
    componentWillReceiveProps(nextProps) {
        let newUser = nextProps.user;
        let oldUser = this.props.user;
        let userChange = newUser !== oldUser;
        if ( newUser && userChange ) {
            this.props.onLoginSuccess(nextProps.user);
        }
        this.setState({
            loading: false
        } );
    },
    getInitialState() {
        return {
            loading: false,
            username: '',
            password: ''
        };
    },
    renderError() {
        let error = this.props.loginError;
        if (error) {
            return (
                <Alert bsStyle="danger" key="errorMessage">
                    <strong>{this.props.loginFailedMessage}</strong> {this.renderErrorText(error)}
                </Alert>
            );
        }
        return null;
    },
    renderErrorText(error) {
        return this.props.loginFailedStatusMessages[error.status] || error.status;
    },
    renderLoading() {
        return this.state.loading ? <Spinner spinnerName="circle" key="loadingSpinner" noFadeIn overrideSpinnerClassName="spinner"/> : null;
    },
    renderSubmit() {
        if (this.props.showSubmitButton) {
            return (<Button
                type="submit"
                value={LocaleUtils.getMessageById(this.context.messages, "user.signIn")}
                bsStyle="primary"
                key="submit" onClick={this.handleSubmit}/>);
        }
    },
    render() {
        return (
            <form ref="loginForm">
                <FormGroup>
                    <ControlLabel>{this.props.userNameText}</ControlLabel>
                    <FormControl ref="username"
                        key="username"
                        type="text"
                        value={this.state.username}
                        placeholder={LocaleUtils.getMessageById(this.context.messages, "user.username")}
                        onChange={this.setUser} />
                </FormGroup>
                <FormGroup>
                    <ControlLabel>{this.props.passwordText}</ControlLabel>
                    <FormControl ref="password"
                        key="password"
                        type="password"
                        value={this.state.password}
                        onKeyPress={this.handleKeyPress}
                        placeholder={LocaleUtils.getMessageById(this.context.messages, "user.password")}
                        onChange={this.setPassword} />
                </FormGroup>
                {this.renderSubmit()}
                {this.renderError()}
                <div style={{"float": "right"}}>{this.renderLoading()}</div>
            </form>
        );
    },
    setUser(e) {
        this.setState({
            username: e.target.value
        });
    },
    setPassword(e) {
        this.setState({
            password: e.target.value
        });
    },
    handleSubmit(e) {
        e.preventDefault();
        this.submit();
    },
    handleKeyPress(target) {
        if (target.charCode === 13) {
            this.submit();
        }

    },
    submit() {
        let username = this.state.username;
        let password = this.state.password;
        if (!username || !password) {
            this.props.onError({status: 0});
        }
        this.props.onSubmit(username, password);
        this.setState({loading: true});
    }
});

module.exports = LoginForm;
