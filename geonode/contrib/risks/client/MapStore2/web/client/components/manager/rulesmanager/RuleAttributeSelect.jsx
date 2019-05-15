/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const Select = require('react-select');
const {Button} = require('react-bootstrap');
const Message = require('../../I18N/Message');

const LocaleUtils = require('../../../utils/LocaleUtils');

require('react-select/dist/react-select.css');

const RuleAttributeSelect = React.createClass({
    propTypes: {
        loadOptions: React.PropTypes.func,
        onInputChange: React.PropTypes.func,
        onValueUpdated: React.PropTypes.func,
        options: React.PropTypes.array,
        placeholderMsgId: React.PropTypes.string,
        selectedValue: React.PropTypes.string,
        className: React.PropTypes.string,
        disabled: React.PropTypes.bool,
        paginated: React.PropTypes.bool,
        currentPage: React.PropTypes.number,
        valuesCount: React.PropTypes.number,
        clearable: React.PropTypes.bool,
        staticValues: React.PropTypes.bool
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getInitialState() {
        return {
            loading: false
        };
    },
    getDefaultProps() {
        return {
            loadOptions: () => {},
            onInputChange: () => {},
            onValueUpdated: () => {},
            options: [],
            disabled: false,
            paginated: false,
            paginationInfo: {},
            currentPage: 0,
            valuesCount: 0,
            clearable: true,
            staticValues: false
        };
    },
    componentWillReceiveProps() {
        this.setState({loading: false});
    },
    getOptions() {
        return this.props.options.map(option => {
            return { value: option, label: option };
        });
    },
    renderPagination() {
        const numberOfPages = Math.ceil(this.props.valuesCount / 10);
        const firstPage = this.props.currentPage === 1 || !this.props.currentPage;
        const lastPage = this.props.currentPage === numberOfPages || !this.props.currentPage;
        return (
            <div style={{textAlign: "center"}}>
                { !firstPage &&
                    <Button
                        bsSize="small"
                        bsStyle="link"
                        onClick={() => this.props.loadOptions(this.props.currentPage - 1)}>
                        <Message msgId="rulesmanager.previous"/>
                    </Button>
                }
                { !lastPage &&
                    <Button
                        bsSize="small"
                        bsStyle="link" onClick={() => this.props.loadOptions(this.props.currentPage + 1)}>
                        <Message msgId="rulesmanager.next"/>
                    </Button>
                }
            </div>
        );
    },
    renderOption(option) {
        return <span>{option.label} {option.pagination}</span>;
    },
    renderValue(option) {
        return <strong>{option.label}</strong>;
    },
    render() {
        let selectedValue;
        if (this.props.selectedValue && this.props.selectedValue !== "*") {
            selectedValue = {
                'value': this.props.selectedValue,
                'label': this.props.selectedValue
            };
        }
        let options = this.getOptions().slice(0);
        if (this.props.paginated && options.length > 0) {
            options.push({ label: '', value: '', disabled: true, pagination: this.renderPagination() });
        }
        return (
            <Select
                isLoading={this.state.loading}
                className={this.props.className}
                onOpen={() => {
                    if (!this.props.staticValues) {
                        this.setState({loading: true});
                    }
                    this.props.loadOptions();
                }}
                searchable={true}
                matchPos="any"
                matchProp="any"
                clearable={this.props.clearable}
                onInputChange={(input) => {
                    this.props.onInputChange(input);
                }}
                options={this.state.loading ? [] : options}
                value={selectedValue}
                onChange={this.props.onValueUpdated}
                disabled={this.props.disabled}
                optionRenderer={this.renderOption}
                valueRenderer={this.renderValue}
                filterOption={this.props.paginated ? () => true : undefined}
                placeholder={LocaleUtils.getMessageById(this.context.messages,
                    this.props.placeholderMsgId || "")}/>
        );
    }
});

module.exports = RuleAttributeSelect;
