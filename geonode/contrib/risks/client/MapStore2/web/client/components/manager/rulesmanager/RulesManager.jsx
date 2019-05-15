/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const RulesTablePanel = require('./RulesTablePanel');
const RulesFiltersPanel = require('./RulesFiltersPanel');
const ActiveRuleModal = require('./ActiveRuleModal');

require('./RulesManager.css');

const RulesManager = React.createClass({
    propTypes: {
        onSelectRules: React.PropTypes.func,
        moveRules: React.PropTypes.func,
        moveRulesToPage: React.PropTypes.func,
        loadRules: React.PropTypes.func,
        rules: React.PropTypes.array,
        rulesPage: React.PropTypes.number,
        rulesCount: React.PropTypes.number,
        selectedRules: React.PropTypes.array,
        rulesTableError: React.PropTypes.string,
        updateActiveRule: React.PropTypes.func,
        deleteRules: React.PropTypes.func,
        addRule: React.PropTypes.func,
        updateRule: React.PropTypes.func,
        loadRoles: React.PropTypes.func,
        loadUsers: React.PropTypes.func,
        loadWorkspaces: React.PropTypes.func,
        loadLayers: React.PropTypes.func,
        options: React.PropTypes.object,
        services: React.PropTypes.object,
        activeRule: React.PropTypes.object,
        updateFiltersValues: React.PropTypes.func,
        filtersValues: React.PropTypes.object,
        error: React.PropTypes.object
    },
    render() {
        return (
            <div>
                <RulesFiltersPanel
                    loadRoles={this.props.loadRoles}
                    loadUsers={this.props.loadUsers}
                    loadWorkspaces={this.props.loadWorkspaces}
                    loadLayers={this.props.loadLayers}
                    options={this.props.options}
                    services={this.props.services}
                    updateFiltersValues={this.props.updateFiltersValues}
                    filtersValues={this.props.filtersValues}
                    loadRules={this.props.loadRules}
                    error={this.props.error}/>
                <RulesTablePanel
                    onSelectRules={this.props.onSelectRules}
                    deleteRules={this.props.deleteRules}
                    rules={this.props.rules}
                    selectedRules={this.props.selectedRules}
                    moveRules={this.props.moveRules}
                    moveRulesToPage={this.props.moveRulesToPage}
                    loadRules={this.props.loadRules}
                    rulesPage={this.props.rulesPage}
                    rulesCount={this.props.rulesCount}
                    updateActiveRule={this.props.updateActiveRule}
                    error={this.props.error}/>
                <ActiveRuleModal
                    updateActiveRule={this.props.updateActiveRule}
                    addRule={this.props.addRule}
                    updateRule={this.props.updateRule}
                    loadRoles={this.props.loadRoles}
                    loadUsers={this.props.loadUsers}
                    loadWorkspaces={this.props.loadWorkspaces}
                    loadLayers={this.props.loadLayers}
                    options={this.props.options}
                    services={this.props.services}
                    activeRule={this.props.activeRule}
                    error={this.props.error}/>
            </div>
        );
    }
});

module.exports = RulesManager;
