/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {Panel, Glyphicon} = require('react-bootstrap');

const Dialog = require('../misc/Dialog');

require("./help.css");

/**
 * A panel showning th current selectd help text.
 *
 * Component's properies:
 *  - id: {string}            the components identifier
 *  - helpText: {string}      the text to display
 *  - isVisible: {bool}       flag to steer visibility of the badge
 *  - title (string)          header text of this panel
 */
const HelpTextPanel = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        helpText: React.PropTypes.string,
        isVisible: React.PropTypes.bool,
        title: React.PropTypes.string,
        onClose: React.PropTypes.func,
        asPanel: React.PropTypes.bool,
        closeGlyph: React.PropTypes.string,
        panelStyle: React.PropTypes.object,
        panelClassName: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            id: 'mapstore-helptext-panel',
            isVisible: false,
            title: 'HELP',
            onClose: () => {},
            asPanel: false,
            closeGlyph: "1-close"
        };
    },
    render() {
        const panel = this.props.asPanel ? (<Panel
            header={<span><span className="help-panel-title">{this.props.title}</span><span className="help-panel-close panel-close" onClick={this.props.onClose}></span></span>}>
            {this.props.helpText}
        </Panel>) : (<Dialog id={this.props.id} style={this.props.panelStyle} className={this.props.panelClassName}>
            <span role="header">
                <span className="help-panel-title">{this.props.title}</span>
                <button onClick={this.props.onClose} className="help-panel-close close">{this.props.closeGlyph ? <Glyphicon glyph={this.props.closeGlyph}/> : <span>×</span>}</button>
            </span>
            <span role="body">{this.props.helpText}</span>
        </Dialog>);
        return (
            <div
                id={this.props.id}
                className={this.props.isVisible ? '' : 'hidden'}
                style={{position: "absolute", top: "140px", marginLeft: "8px"}}>
                {panel}
            </div>
        );
    }
});

module.exports = HelpTextPanel;
