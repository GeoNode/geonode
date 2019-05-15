/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {Collapse, Panel, Button, ButtonGroup, Tooltip, OverlayTrigger} = require('react-bootstrap');

const assign = require('object-assign');

const HelpBadge = require('../help/HelpBadge');


/**
 * This toolbar renders as an accordion for big screens, as a
 * toolbar with small screens, rendering the content as a modal
 * window.
 */
let MapToolbar = React.createClass({
    propTypes: {
        layers: React.PropTypes.array,
        panelStyle: React.PropTypes.object,
        containerStyle: React.PropTypes.object,
        propertiesChangeHandler: React.PropTypes.func,
        onActivateItem: React.PropTypes.func,
        activeKey: React.PropTypes.string,
        helpEnabled: React.PropTypes.bool,
        changeHelpText: React.PropTypes.func,
        changeHelpwinVisibility: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            panelStyle: {
                minWidth: "300px",
                right: "52px",
                position: "absolute",
                overflow: "auto"
            },
            containerStyle: {
                position: "absolute",
                top: "5px",
                right: "5px",
                marginRight: "5px",
                marginTop: "5px",
                zIndex: 1000
            }
        };
    },
    getPanelStyle() {
        var width = window.innerWidth
                || document.documentElement.clientWidth
                || document.body.clientWidth;

        var height = window.innerHeight
                || document.documentElement.clientHeight
                || document.body.clientHeight;
        var maxHeight = height - 70; // TODO make it parametric or calculate
        var maxWidth = width - 70; // TODO make it parametric or calculate
        return assign({}, this.props.panelStyle, {maxWidth: maxWidth + "px", maxHeight: maxHeight + "px"});
    },
    render() {
        var children = React.Children.map(this.props.children, (item) => {
            if (item.props.isPanel) {
                return (
                <Collapse key={"mapToolBar-item-collapse-" + item.key} in={this.props.activeKey === item.key}>
                    <Panel header={item.props.title} style={this.getPanelStyle()} >
                        {item}
                    </Panel>
                </Collapse>);
            }
            return null;

        }, this);
        var buttons = React.Children.map(this.props.children, (item) => {
            if (item.props.isPanel) {
                let tooltip = <Tooltip id="toolbar-map-layers-button">{item.props.buttonTooltip}</Tooltip>;
                return (
                    <OverlayTrigger key={"mapToolBar-item-OT-" + item.key} rootClose placement="left" overlay={tooltip}>
                        <Button
                            active={this.props.activeKey === item.key}
                            style={{width: "100%"}}
                            onClick={ () => this.handleSelect(item.key)}>
                                {(item.props.helpText) ? (<HelpBadge
                                    className="mapstore-tb-helpbadge"
                                    helpText={item.props.helpText}
                                    isVisible={this.props.helpEnabled}
                                    changeHelpText={this.props.changeHelpText}
                                    changeHelpwinVisibility={this.props.changeHelpwinVisibility}
                                    />) : null}
                                {item.props.help}
                                {item.props.buttonContent || item.props.icon}
                        </Button>
                    </OverlayTrigger>
                );
            }
            return item;

        }, this);
        return (<div style={this.props.containerStyle}>
            {children}
            <ButtonGroup vertical className="mapToolbar">
                {buttons}
            </ButtonGroup>
            </div>);

    },

    handleSelect(activeKey) {
        if (activeKey === this.props.activeKey) {
            this.props.onActivateItem();
        }else {
            this.props.onActivateItem(activeKey);
        }

    }
});
module.exports = MapToolbar;
