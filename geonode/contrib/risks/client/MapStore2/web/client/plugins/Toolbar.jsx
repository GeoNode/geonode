/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {connect} = require('react-redux');

require('./toolbar/assets/css/toolbar.css');

const ReactCSSTransitionGroup = require('react-addons-css-transition-group');

const assign = require('object-assign');

const ToolsContainer = require('./containers/ToolsContainer');

const AnimatedContainer = connect(() => ({
     transitionName: "toolbarexpand",
     transitionEnterTimeout: 500,
     transitionLeaveTimeout: 300
}))(ReactCSSTransitionGroup);

const Toolbar = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        tools: React.PropTypes.array,
        mapType: React.PropTypes.string,
        style: React.PropTypes.object,
        panelStyle: React.PropTypes.object,
        panelClassName: React.PropTypes.string,
        active: React.PropTypes.string,
        items: React.PropTypes.array,
        allVisible: React.PropTypes.bool,
        layout: React.PropTypes.string,
        stateSelector: React.PropTypes.string,
        buttonStyle: React.PropTypes.string,
        buttonSize: React.PropTypes.string,
        pressedButtonStyle: React.PropTypes.string,
        btnConfig: React.PropTypes.object
    },
    contextTypes: {
        messages: React.PropTypes.object,
        router: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            id: "mapstore-toolbar",
            style: {},
            panelStyle: {
                minWidth: "300px",
                right: "52px",
                zIndex: 100,
                position: "absolute",
                overflow: "auto",
                left: "450px"
            },
            panelClassName: "toolbar-panel",
            items: [],
            allVisible: true,
            layout: "vertical",
            stateSelector: "toolbar",
            buttonStyle: 'primary',
            buttonSize: null,
            pressedButtonStyle: 'success',
            btnConfig: {
                className: "square-button"
            }
        };
    },
    getPanel(tool) {
        if (tool.panel === true) {
            return tool.plugin;
        }
        return tool.panel;
    },
    getPanels() {
        return this.getTools()
            .filter((tool) => tool.panel)
            .map((tool) => ({name: tool.name, title: tool.title, cfg: tool.cfg, panel: this.getPanel(tool), items: tool.items, wrap: tool.wrap || false}));
    },
    getTools() {
        const unsorted = this.props.items
            .filter((item) => item.alwaysVisible || this.props.allVisible)
            .map((item, index) => assign({}, item, {position: item.position || index}));
        return unsorted.sort((a, b) => a.position - b.position);
    },
    render() {
        return (<ToolsContainer id={this.props.id} className={"mapToolbar btn-group-" + this.props.layout}
            toolCfg={this.props.btnConfig}
            container={AnimatedContainer}
            mapType={this.props.mapType}
            toolStyle={this.props.buttonStyle}
            activeStyle={this.props.pressedButtonStyle}
            toolSize={this.props.buttonSize}
            stateSelector={this.props.stateSelector}
            tools={this.getTools()}
            panels={this.getPanels()}
            activePanel={this.props.active}
            style={this.props.style}
            panelStyle={this.props.panelStyle}
            panelClassName={this.props.panelClassName}
            />);
    }
});

module.exports = {
    ToolbarPlugin: (stateSelector = 'toolbar') => (connect((state) => ({
        active: state.controls && state.controls[stateSelector] && state.controls[stateSelector].active,
        allVisible: state.controls && state.controls[stateSelector] && state.controls[stateSelector].expanded,
        stateSelector
    }))(Toolbar)),
    reducers: {controls: require('../reducers/controls')}
};
