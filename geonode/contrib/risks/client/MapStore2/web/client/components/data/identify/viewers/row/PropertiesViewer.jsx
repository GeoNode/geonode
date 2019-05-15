/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');

var PropertiesViewer = React.createClass({
    propTypes: {
        title: React.PropTypes.string,
        exclude: React.PropTypes.array,
        titleStyle: React.PropTypes.object,
        listStyle: React.PropTypes.object,
        componentStyle: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            exclude: [],
            titleStyle: {
                height: "100%",
                width: "100%",
                padding: "4px 0px",
                background: "rgb(240,240,240)",
                borderRadius: "4px",
                textAlign: "center",
                textOverflow: "ellipsis"
            },
            listStyle: {
                margin: "0px 0px 4px 0px"
            },
            componentStyle: {
                padding: "0px 0px 2px 0px",
                margin: "2px 0px 0px 0px"
            }
        };
    },
    getBodyItems() {
        return Object.keys(this.props)
            .filter(this.toExlude)
            .map((key) => {
                return (
                    <p key={key} style={this.props.listStyle}><b>{key}</b> {this.props[key]}</p>
                );
            });
    },
    renderHeader() {
        if (!this.props.title) {
            return null;
        }
        return (
            <div key={this.props.title} style={this.props.titleStyle}>
                {this.props.title}
            </div>
        );
    },
    renderBody() {
        var items = this.getBodyItems();
        if (items.length === 0) {
            return null;
        }
        return (
            <div style={{
                padding: "4px",
                margin: 0,
                borderRadius: "4px",
                boxShadow: "0px 2px 1px rgb(240,240,240)"
            }}>
                {items}
            </div>
        );
    },
    render() {
        return (
            <div style={this.props.componentStyle}>
                {this.renderHeader()}
                {this.renderBody()}
            </div>
        );
    },
    alwaysExcluded: ["exclude", "titleStyle", "listStyle", "componentStyle", "title"],
    toExlude(propName) {
        return this.alwaysExcluded
            .concat(this.props.exclude)
            .indexOf(propName) === -1;
    }
});

module.exports = PropertiesViewer;
