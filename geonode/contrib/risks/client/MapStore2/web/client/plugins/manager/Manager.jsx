/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const { itemSelected } = require('../../actions/manager');
const {Nav, NavItem, Glyphicon} = require('react-bootstrap');
const {connect} = require('react-redux');
const {Message} = require('../../components/I18N/I18N');
require('./style/manager.css');

const Manager = React.createClass({
    propTypes: {
        navStyle: React.PropTypes.object,
        items: React.PropTypes.array,
        itemSelected: React.PropTypes.func,
        selectedTool: React.PropTypes.string
    },
    contextTypes: {
        router: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            items: [],
            mapType: "openlayers",
            selectedTool: "importer",
            itemSelected: () => {},
            navStyle: {
              flex: "inherit"
            }
        };
    },
    renderToolIcon(tool) {
        if (tool.glyph) {
            return <Glyphicon glyph={tool.glyph} />;
        }
    },
    renderNavItems() {
        return this.props.items.map((tool) =>
            (<NavItem
                eventKey={tool.id}
                key={tool.id}
                href="#"
                onClick={(event) => {
                    event.preventDefault();
                    this.props.itemSelected(tool.id);
                    this.context.router.push("/manager/" + tool.id);
                }}>
                    {this.renderToolIcon(tool)}
                    <span className="nav-msg">&nbsp;{tool.msgId ? <Message msgId={tool.msgId} /> : tool.title || tool.id}</span>
            </NavItem>));
    },
    renderPlugin() {
        for ( let i = 0; i < this.props.items.length; i++) {
            let tool = this.props.items[i];
            if (tool.id === this.props.selectedTool) {
                return <tool.plugin key={tool.id} {...tool.cfg} />;
            }
        }
        return null;

    },
    render() {
        return (<div className="Manager-Container">
            <Nav className="Manager-Tools-Nav" bsStyle="pills" stacked activeKey={this.props.selectedTool} style={this.props.navStyle}>
                {this.renderNavItems()}
            </Nav>
            <div style={{
                flex: 1
            }}>{this.renderPlugin()} </div>
        </div>);
    }
});

module.exports = {
    ManagerPlugin: connect((state, ownProps) => ({
        selectedTool: ownProps.tool
    }),
    {
        itemSelected
    })(Manager)
};
