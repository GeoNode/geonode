/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Glyphicon, OverlayTrigger, Tooltip} = require('react-bootstrap');
const Message = require('../../I18N/Message');

require("./css/layertool.css");


const LayersTool = React.createClass({
    propTypes: {
        node: React.PropTypes.object,
        onClick: React.PropTypes.func,
        style: React.PropTypes.object,
        glyph: React.PropTypes.string,
        tooltip: React.PropTypes.string,
        className: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            onClick: () => {}
        };
    },
    render() {
        const cn = this.props.className ? " " + this.props.className : "";
        const tool = (<Glyphicon className={"toc-layer-tool" + cn} style={this.props.style}
                   glyph={this.props.glyph}
                   onClick={(options) => this.props.onClick(this.props.node, options || {})}/>);
        return this.props.tooltip ? (
           <OverlayTrigger placement="bottom" overlay={(<Tooltip id={"Tooltip-" + this.props.tooltip}><strong><Message msgId={this.props.tooltip}/></strong></Tooltip>)}>
               {tool}
           </OverlayTrigger>) : tool;

    }
});

module.exports = LayersTool;
