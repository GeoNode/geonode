/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {connect} = require('react-redux');

const {Button, Grid, Col} = require('react-bootstrap');
const Message = require('../components/I18N/Message');


const CreateNewMap = React.createClass({
    propTypes: {
        mapType: React.PropTypes.string,
        onGoToMap: React.PropTypes.func,
        colProps: React.PropTypes.object,
        isLoggedIn: React.PropTypes.bool
    },
    contextTypes: {
        router: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            mapType: "leaflet",
            isLoggedIn: false,
            onGoToMap: () => {},
            colProps: {
                xs: 12,
                sm: 12,
                lg: 12,
                md: 12
            }
        };
    },

    render() {
        const display = this.props.isLoggedIn ? null : "none";
        return (<Grid fluid={true} style={{marginBottom: "30px", padding: 0, display}}>
        <Col {...this.props.colProps} >
            <Button bsStyle="primary" onClick={() => { this.context.router.push("/viewer/" + this.props.mapType + "/new"); }}>
            <Message msgId="newMap" />
            </Button>
        </Col>
        </Grid>);
    }
});

module.exports = {
    CreateNewMapPlugin: connect((state) => ({
        mapType: (state.maps && state.maps.mapType) || (state.home && state.home.mapType),
        isLoggedIn: state && state.security && state.security.user && state.security.user.enabled && true || false
    }))(CreateNewMap)
};
