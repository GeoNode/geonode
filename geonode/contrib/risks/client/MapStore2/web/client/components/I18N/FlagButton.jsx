
/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var {Button, Tooltip, OverlayTrigger} = require('react-bootstrap');
var LocaleUtils = require('../../utils/LocaleUtils');


var LangBar = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        lang: React.PropTypes.string,
        code: React.PropTypes.string,
        active: React.PropTypes.bool,
        label: React.PropTypes.string,
        description: React.PropTypes.string,
        onFlagSelected: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            locales: LocaleUtils.getSupportedLocales(),
            code: 'en-US',
            onLanguageChange: function() {}
        };
    },
    render() {
        let tooltip = <Tooltip id={"flag-button." + this.props.code}>{this.props.label}</Tooltip>;
        return (<OverlayTrigger key={"overlay-" + this.props.code} overlay={tooltip}>
            <Button
                key={this.props.code}
                onClick={this.launchFlagAction.bind(this, this.props.code)}
                active={this.props.active}>
                <img src={require('./images/flags/' + this.props.code + '.png')} alt={this.props.label}/>
            </Button>
        </OverlayTrigger>);
    },
    launchFlagAction(code) {
        this.props.onFlagSelected(code);
    }
});

module.exports = LangBar;
