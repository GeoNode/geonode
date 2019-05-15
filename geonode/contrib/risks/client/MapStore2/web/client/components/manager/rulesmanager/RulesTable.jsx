/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Table} = require('react-bootstrap');
const _ = require('lodash');

const RulesTableElement = require('./RulesTableElement');
const LocaleUtils = require('../../../utils/LocaleUtils');

const dragDropContext = require('react-dnd').DragDropContext;
const html5Backend = require('react-dnd-html5-backend');

const RulesTable = React.createClass({
    propTypes: {
        onSelectRules: React.PropTypes.func,
        rules: React.PropTypes.array,
        selectedRules: React.PropTypes.array,
        moveRules: React.PropTypes.func
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            onSelectRules: () => {},
            rules: [],
            selectedRules: []
        };
    },
    render() {
        const allChecked = this.props.selectedRules.length !== 0 &&
            this.props.selectedRules.length === this.props.rules.length;
        return (
            <Table className="rules-table" bordered condensed hover>
                <thead>
                    <tr>
                        <th>
                            <input
                                type="checkbox"
                                checked={allChecked}
                                onChange={() => this.props.onSelectRules(
                                    this.props.rules, true, allChecked)}/>
                        </th>
                        <th>{this.locale("role")}</th>
                        <th>{this.locale("user")}</th>
                        <th>{this.locale("service")}</th>
                        <th>{this.locale("request")}</th>
                        <th>{this.locale("workspace")}</th>
                        <th>{this.locale("layer")}</th>
                        <th>{this.locale("access")}</th>
                    </tr>
                </thead>
                <tbody>
                    {this.props.rules.map((rule, index) => {
                        const checked = this.isChecked(rule, this.props.selectedRules);
                        return (<RulesTableElement
                            moveRules={this.props.moveRules}
                            onSelect={() => this.props.onSelectRules([rule], true, checked)}
                            rule={rule}
                            checked={checked}
                            key={index}
                            sortData={index}
                            isDraggable={true}/>);
                    })}
                </tbody>
            </Table>
        );
    },
    locale(messageId) {
        return LocaleUtils.getMessageById(
            this.context.messages, "rulesmanager." + messageId);
    },
    handleSort(sorted) {
        return function() {
            if (!sorted) {
                return;
            }
            for (let i = 0; i < sorted.length; i++) {
                if (sorted[i] !== i) {
                    const movedRule = this.props.rules[sorted[i]];
                    const targetRule = this.props.rules[i];
                    this.props.moveRules(targetRule.priority, [movedRule.id]);
                }
            }
        }.bind(this);
    },
    isChecked(rule, selectedRules) {
        return _.find(selectedRules, (selectedRule) => selectedRule.id === rule.id) !== undefined;
    }
});

module.exports = dragDropContext(html5Backend)(RulesTable);
