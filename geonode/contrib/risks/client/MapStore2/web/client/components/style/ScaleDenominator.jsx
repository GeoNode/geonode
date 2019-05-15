/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const mapUtils = require('../../utils/MapUtils');
const {findDOMNode} = require('react-dom');
const DropdownList = require('react-widgets').DropdownList;
const {Row, Col, Overlay, Popover, Label} = require('react-bootstrap');
const LocaleUtils = require('../../utils/LocaleUtils');
const Message = require('../I18N/Message');

const ScaleDenominator = React.createClass({
    propTypes: {
        minValue: React.PropTypes.number,
        maxValue: React.PropTypes.number,
        onChange: React.PropTypes.func.isRequired
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getInitialState() {
        return {error: false};
    },
    getDefaultProps() {
        return {
            minValue: null,
            maxValue: null,
            onChange: () => null
        };
    },
    componentWillMount() {
        let scales = mapUtils.getGoogleMercatorScales(0, 21);
        this.scales = [{value: null, text: LocaleUtils.getMessageById(this.context.messages, "scaledenominator.none") || 'None'}, ...scales.map((v) => ({value: v, text: `${v.toFixed(0)}`}))];
    },
    onChange(t, {value: v}) {
        if (t === 'minDenominator' && this.props.maxValue && v >= this.props.maxValue) {
            this.setState({error: {type: t, msg: "scaledenominator.minerror"}});
        }else if (t === 'maxDenominator' && this.props.minValue && v <= this.props.minValue) {
            this.setState({error: {type: t, msg: "scaledenominator.maxerror"}});
        }else {
            if (this.state.error) {
                this.setState({error: false});
            }
            this.props.onChange(t, v);
        }
    },
    renderErrorPopOver() {
        return (
            <Overlay
            target={() => findDOMNode(this.refs[this.state.error.type])}
                show={true} placement="top" >
                <Popover id={`${this.state.error.type}_id`}>
                    <Label bsStyle="danger" > <Message msgId={this.state.error.msg}/></Label>
                </Popover>
            </Overlay>
            );
    },
    render() {
        return (<Row>
            <Col xs={6}>
            <label><Message msgId="scaledenominator.minlabel"/></label>
            <DropdownList
                ref="minDenominator"
                data={this.scales}
                value={this.props.minValue}
                valueField="value"
                textField="text"
                onChange={(v) => this.onChange("minDenominator", v)}
            />
            </Col>
            <Col xs={6}>
            <label><Message msgId="scaledenominator.maxlabel"/></label>
            <DropdownList
                ref="maxDenominator"
                data={this.scales}
                value={this.props.maxValue}
                valueField="value"
                textField="text"
                onChange={(v) => this.onChange("maxDenominator", v)}
            />
            </Col>
            {(this.state.error) ? this.renderErrorPopOver() : null}
            </Row>
            );
    }
});

module.exports = ScaleDenominator;
