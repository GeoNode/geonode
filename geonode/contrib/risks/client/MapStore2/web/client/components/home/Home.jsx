/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {Glyphicon, OverlayTrigger, Tooltip, Button} = require('react-bootstrap');
const Message = require('../../components/I18N/Message');

const Home = React.createClass({
    propTypes: {
        icon: React.PropTypes.node
    },
    contextTypes: {
        router: React.PropTypes.object,
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            icon: <Glyphicon glyph="home"/>
        };
    },
    render() {
        let tooltip = <Tooltip id="toolbar-home-button">{<Message msgId="gohome"/>}</Tooltip>;
        return (
            <OverlayTrigger overlay={tooltip}>
            <Button
                {...this.props}
                id="home-button"
                className="square-button"
                bsStyle="primary"
                onClick={this.goHome}
                tooltip={tooltip}
                >{this.props.icon}</Button>
        </OverlayTrigger>
        );
    },
    goHome() {
        this.context.router.push("/");
    }
});
module.exports = Home;
