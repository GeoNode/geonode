/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {isFunction} = require('lodash');
const LayersTool = require('./LayersTool');
require("./css/visibilitycheck.css");

const VisibilityCheck = React.createClass({
    propTypes: {
        node: React.PropTypes.object,
        tooltip: React.PropTypes.string,
        propertiesChangeHandler: React.PropTypes.func,
        style: React.PropTypes.object,
        checkType: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.func]),
        glyphChecked: React.PropTypes.string,
        glyphUnchecked: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            style: {},
            checkType: "glyph",
            glyphChecked: "eye-open",
            tooltip: "toc.toggleLayerVisibility",
            glyphUnchecked: "eye-close"
        };
    },
    render() {
        if (this.props.checkType === "glyph") {
            return (<LayersTool
                tooltip={this.props.tooltip}
                style={this.props.style}
                className={"visibility-check" + (this.props.node.visibility ? " checked" : "")}
                data-position={this.props.node.storeIndex}
                glyph={this.props.node.visibility ? this.props.glyphChecked : this.props.glyphUnchecked}
                onClick={this.changeVisibility}
                />);
        }
        return (<input className="visibility-check" style={this.props.style}
            data-position={this.props.node.storeIndex}
            type={isFunction(this.props.checkType) ? this.props.checkType(this.props.node) : this.props.checkType}
            checked={this.props.node.visibility ? "checked" : ""}
            onChange={this.changeVisibility} />);
    },
    changeVisibility() {
        this.props.propertiesChangeHandler(this.props.node.id, {visibility: !this.props.node.visibility});
    }
});

module.exports = VisibilityCheck;
