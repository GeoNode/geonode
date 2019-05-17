/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {Glyphicon, Tooltip} = require('react-bootstrap');
const ToggleButton = require('../../../components/buttons/ToggleButton');
const Message = require('../../../components/I18N/Message');

const Home = React.createClass({
    propTypes: {
        isPanel: React.PropTypes.bool,
        buttonTooltip: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        help: React.PropTypes.object,
        changeHelpText: React.PropTypes.func,
        changeHelpwinVisibility: React.PropTypes.func
    },
    contextTypes: {
        router: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            isPanel: false,
            icon: <Glyphicon glyph="home"/>
        };
    },
    render() {
        let tooltip = <Tooltip id="toolbar-home-button">{this.props.buttonTooltip}</Tooltip>;
        return (
            <ToggleButton
                id="home-button"
                key="gohome"
                isButton={true}
                pressed={false}
                glyphicon="home"
                helpText={<Message msgId="helptexts.gohome"/>}
                onClick={this.goHome}
                tooltip={tooltip}
                tooltipPlace="left"
                />
        );
    },
    goHome() {
        this.context.router.push("/");
    }
});
module.exports = Home;
