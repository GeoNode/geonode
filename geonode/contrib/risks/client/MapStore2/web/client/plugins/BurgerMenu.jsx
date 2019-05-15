/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {connect} = require('react-redux');

const assign = require('object-assign');

const {DropdownButton, Glyphicon, MenuItem} = require('react-bootstrap');

const Container = connect(() => ({
    noCaret: true,
    pullRight: true,
    bsStyle: "primary",
    title: <Glyphicon glyph="menu-hamburger"/>
}))(DropdownButton);

const ToolsContainer = require('./containers/ToolsContainer');
const Message = require('./locale/Message');

require('./burgermenu/burgermenu.css');

const BurgerMenu = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        dispatch: React.PropTypes.func,
        items: React.PropTypes.array,
        title: React.PropTypes.node,
        onItemClick: React.PropTypes.func,
        controls: React.PropTypes.object,
        mapType: React.PropTypes.string,
        panelStyle: React.PropTypes.object,
        panelClassName: React.PropTypes.string
    },
    contextTypes: {
        messages: React.PropTypes.object,
        router: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            id: "mapstore-burger-menu",
            items: [],
            onItemClick: () => {},
            title: <MenuItem header><Message msgId="options"/></MenuItem>,
            controls: [],
            mapType: "leaflet",
            panelStyle: {
                minWidth: "300px",
                right: "52px",
                zIndex: 100,
                position: "absolute",
                overflow: "auto"
            },
            panelClassName: "toolbar-panel"
        };
    },
    getPanels() {
        return this.props.items.filter((item) => item.panel)
            .map((item) => assign({}, item, {panel: item.panel === true ? item.plugin : item.panel})).concat(
                this.props.items.filter((item) => item.tools).reduce((previous, current) => {
                    return previous.concat(
                        current.tools.map((tool, index) => ({
                            name: current.name + index,
                            panel: tool,
                            cfg: current.cfg.toolsCfg ? current.cfg.toolsCfg[index] : {}
                        }))
                    );
                }, [])
            );
    },
    getTools() {
        return [{element: <span key="burger-menu-title">{this.props.title}</span>}, ...this.props.items.sort((a, b) => a.position - b.position)];
    },
    render() {
        return (
            <ToolsContainer id={this.props.id} className="square-button"
                container={Container}
                mapType={this.props.mapType}
                toolStyle="primary"
                activeStyle="default"
                stateSelector="burgermenu"
                eventSelector="onSelect"
                tool={MenuItem}
                tools={this.getTools()}
                panels={this.getPanels()}
                panelStyle={this.props.panelStyle}
                panelClassName={this.props.panelClassName}
            />);
    }
});

module.exports = {
    BurgerMenuPlugin: assign(connect((state) => ({
        controls: state.controls
    }))(BurgerMenu), {
        OmniBar: {
            name: "burgermenu",
            position: 2,
            tool: true,
            priority: 1
        }
    }),
    reducers: {}
};
