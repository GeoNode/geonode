/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const assign = require('object-assign');
const {connect} = require('react-redux');

const RedirectComponent = React.createClass({
    propTypes: {
        userDetails: React.PropTypes.object
    },
    contextTypes: {
        router: React.PropTypes.object
    },
    componentDidMount() {
        this.redirect(this.props);
    },
    componentWillReceiveProps(nextProps) {
        this.redirect(nextProps);
    },
    render() {
        return null;
    },
    redirect(props) {
        if (!props.userDetails || !props.userDetails.user) {
            this.context.router.push("/");
        }
    }
});

const Redirect = connect((state) => ({
    userDetails: state.security || null
}))(RedirectComponent);


module.exports = {
    RedirectPlugin: assign(Redirect, {}
)};
