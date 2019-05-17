/**
* Copyright 2016, GeoSolutions Sas.
* All rights reserved.
*
* This source code is licensed under the BSD-style license found in the
* LICENSE file in the root directory of this source tree.
*/
const React = require('react');
const {connect} = require('react-redux');
const {geoStoreLoginSubmit, loginFail, logoutWithReload, geoStoreChangePassword, resetError} = require('../../actions/security');
const {setControlProperty} = require('../../actions/controls');
const {Glyphicon} = require('react-bootstrap');

const closeLogin = () => {
    return (dispatch) => {
        dispatch(setControlProperty('LoginForm', 'enabled', false));
        dispatch(resetError());
    };
};

const UserMenu = connect((state) => ({
    user: state.security && state.security.user
}), {
    onShowLogin: setControlProperty.bind(null, "LoginForm", "enabled", true, true),
    onShowAccountInfo: setControlProperty.bind(null, "AccountInfo", "enabled", true, true),
    onShowChangePassword: setControlProperty.bind(null, "ResetPassword", "enabled", true, true),
    onLogout: logoutWithReload
})(require('../../components/security/UserMenu'));

const UserDetails = connect((state) => ({
    user: state.security && state.security.user,
    show: state.controls.AccountInfo && state.controls.AccountInfo.enabled}
), {
    onClose: setControlProperty.bind(null, "AccountInfo", "enabled", false, false)
})(require('../../components/security/modals/UserDetailsModal'));

const PasswordReset = connect((state) => ({
    user: state.security && state.security.user,
    show: state.controls.ResetPassword && state.controls.ResetPassword.enabled
}), {
    onPasswordChange: (user, pass) => { return geoStoreChangePassword(user, pass); },
    onClose: setControlProperty.bind(null, "ResetPassword", "enabled", false, false)
})(require('../../components/security/modals/PasswordResetModal'));

const Login = connect((state) => ({
    show: state.controls.LoginForm && state.controls.LoginForm.enabled,
    user: state.security && state.security.user,
    loginError: state.security && state.security.loginError
}), {
    onLoginSuccess: setControlProperty.bind(null, 'LoginForm', 'enabled', false, false),
    onClose: closeLogin,
    onSubmit: geoStoreLoginSubmit,
    onError: loginFail
})(require('../../components/security/modals/LoginModal'));

const LoginNav = connect((state) => ({
    user: state.security && state.security.user,
    nav: false,
    renderButtonText: false,
    renderButtonContent: () => {return <Glyphicon glyph="user" />; },
    bsStyle: "primary",
    className: "square-button"
}), {
    onShowLogin: setControlProperty.bind(null, "LoginForm", "enabled", true, true),
    onShowAccountInfo: setControlProperty.bind(null, "AccountInfo", "enabled", true, true),
    onShowChangePassword: setControlProperty.bind(null, "ResetPassword", "enabled", true, true),
    onLogout: logoutWithReload
})(require('../../components/security/UserMenu'));

module.exports = {
    UserDetails,
    UserMenu,
    PasswordReset,
    Login,
    LoginNav
};
