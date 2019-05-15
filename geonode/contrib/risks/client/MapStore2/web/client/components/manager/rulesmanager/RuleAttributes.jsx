/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Panel} = require('react-bootstrap');
const _ = require('lodash');
const Select = require('./RuleAttributeSelect');
const {head} = require('lodash');

const ACCESS_TYPES = [
    'ALLOW',
    'DENY'
];

const RuleAttributes = React.createClass({
    propTypes: {
        loadRoles: React.PropTypes.func,
        loadUsers: React.PropTypes.func,
        loadWorkspaces: React.PropTypes.func,
        loadLayers: React.PropTypes.func,
        panelHeader: React.PropTypes.string,
        options: React.PropTypes.object,
        services: React.PropTypes.object,
        updateRuleAttributes: React.PropTypes.func,
        ruleAttributes: React.PropTypes.object,
        showAccess: React.PropTypes.bool,
        containerClassName: React.PropTypes.string,
        selectClassName: React.PropTypes.string,
        context: React.PropTypes.string
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            loadRoles: () => {},
            loadUsers: () => {},
            loadWorkspaces: () => {},
            loadLayers: () => {},
            options: {},
            updateRuleAttributes: () => {},
            ruleAttributes: {},
            showAccess: false,
            services: {}
        };
    },
    getServicesNames() {
        return Object.keys(this.props.services);
    },
    getRequestsNames() {
        if (this.props.ruleAttributes.service) {
            return this.props.services[this.props.ruleAttributes.service];
        }
        const keys = Object.keys(this.props.services);
        return _(keys.map(key => this.props.services[key])).flatten().uniq().value();
    },
    render() {
        const requestNames = this.getRequestsNames() || [];
        const selectedWorkSpace = this.props.ruleAttributes.workspace;
        return (
            <Panel header={this.props.panelHeader} className={this.props.containerClassName}>
                <Select
                    loadOptions={() => this.props.loadRoles(this.props.context)}
                    onValueUpdated={this.createUpdateFunction('roleName')}
                    selectedValue={this.props.ruleAttributes.roleName}
                    placeholderMsgId={'rulesmanager.role'}
                    options={this.props.options.roles}
                    className={this.props.selectClassName}/>
                <Select
                    loadOptions={() => this.props.loadUsers(this.props.context)}
                    onValueUpdated={this.createUpdateFunction('userName')}
                    selectedValue={this.props.ruleAttributes.userName}
                    placeholderMsgId={'rulesmanager.user'}
                    options={this.props.options.users}
                    className={this.props.selectClassName}/>
                <Select
                    onValueUpdated={this.createUpdateFunction('service', 'request')}
                    selectedValue={this.props.ruleAttributes.service}
                    placeholderMsgId={'rulesmanager.service'}
                    options={this.getServicesNames()}
                    className={this.props.selectClassName}
                    staticValues={true}/>
                <Select
                    onValueUpdated={this.createUpdateFunction('request')}
                    selectedValue={this.props.ruleAttributes.service && this.props.ruleAttributes.request}
                    placeholderMsgId={'rulesmanager.request'}
                    options={requestNames}
                    className={this.props.selectClassName}
                    disabled={this.isNullValue(this.props.ruleAttributes.service)}
                    staticValues={true}/>
                <Select loadOptions={() => this.props.loadWorkspaces(this.props.context)}
                    onValueUpdated={this.createUpdateFunction('workspace', 'layer')}
                    selectedValue={selectedWorkSpace}
                    placeholderMsgId={'rulesmanager.workspace'}
                    options={this.props.options.workspaces}
                    className={this.props.selectClassName}/>
                <Select loadOptions={(page) =>
                        this.props.loadLayers(undefined, selectedWorkSpace, page || 1, this.props.context)}
                    onInputChange={(input, page) =>
                        this.props.loadLayers(input, selectedWorkSpace, page || 1, this.props.context)}
                    onValueUpdated={this.createUpdateFunction('layer')}
                    selectedValue={selectedWorkSpace && this.props.ruleAttributes.layer}
                    placeholderMsgId={'rulesmanager.layer'}
                    options={this.props.options.layers}
                    className={this.props.selectClassName}
                    disabled={this.isNullValue(this.props.ruleAttributes.workspace)}
                    paginated={true}
                    currentPage={this.props.options.layersPage}
                    valuesCount={this.props.options.layersCount}/>
                {
                    this.props.showAccess &&
                    <Select onValueUpdated={this.createUpdateFunction('access')}
                        selectedValue={this.props.ruleAttributes.access || ACCESS_TYPES[0]}
                        placeholderMsgId={'rulesmanager.access'}
                        options={ACCESS_TYPES}
                        clearable={false}
                        className={this.props.selectClassName}
                        staticValues={true}/>
                }
            </Panel>
        );
    },
    filterValue(value, values) {
        if (value && head(values.filter(existing => existing === value))) {
            return value;
        }
        return undefined;
    },
    createUpdateFunction(attributeName, attributeNameToReset) {
        return function(attributeValue) {
            if (!attributeNameToReset) {
                this.props.updateRuleAttributes(
                    {[attributeName]: attributeValue ? attributeValue.value : "*"});
            } else {
                this.props.updateRuleAttributes(
                    {[attributeName]: attributeValue ? attributeValue.value : "*",
                     [attributeNameToReset]: undefined});
            }
        }.bind(this);
    },
    isNullValue(value) {
        return value === undefined || value === "*";
    }
});

module.exports = RuleAttributes;
