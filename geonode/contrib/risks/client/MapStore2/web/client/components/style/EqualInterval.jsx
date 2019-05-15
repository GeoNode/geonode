/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */


const React = require('react');
const {findDOMNode} = require('react-dom');
const {Grid, Row, Col, Button, Popover, Label, Overlay} = require('react-bootstrap');

const Combobox = require('react-widgets').Combobox;
const numberLocalizer = require('react-widgets/lib/localizers/simple-number');
numberLocalizer();
const {NumberPicker} = require('react-widgets');

const ColorRampItem = require('./EqualIntervalComponents/ColorRampItem');
const colorsSchema = require("./EqualIntervalComponents/ColorRamp");
const colors = require("./EqualIntervalComponents/ExtendColorBrewer");

const Message = require('../I18N/Message');

const EqualInterval = React.createClass({
    propTypes: {
        min: React.PropTypes.number,
        max: React.PropTypes.number,
        classes: React.PropTypes.number,
        onChange: React.PropTypes.func,
        onClassify: React.PropTypes.func,
        ramp: React.PropTypes.string,
        error: React.PropTypes.object
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            min: 0,
            max: 100,
            classes: 5,
            ramp: "Blues",
            onChange: () => {},
            onClassify: () => {},
            error: null
        };
    },
    shouldComponentUpdate() {
        return true;
    },
    getColorsSchema() {
        return (this.props.classes) ?
            colorsSchema.filter((c) => {
                return c.max >= this.props.classes;
            }, this) : colorsSchema;
    },
    getRampValue() {
        let ramp = this.props.ramp;
        if (!colors[this.props.ramp][this.props.classes]) {
            ramp = colorsSchema.filter((color) => { return color.max >= this.props.classes; }, this)[0].name;
        }
        return ramp;
    },
    renderErrorPopOver() {
        return (
            <Overlay
            target={() => findDOMNode(this.refs[this.props.error.type])}
                show={true} placement="top" >
                <Popover>
                    <Label bsStyle="danger" > <Message msgId={this.props.error.msg}/></Label>
                </Popover>
            </Overlay>
            );
    },
    render() {
        return (
            <Grid fluid>
                <Row>
                    <Col xs={4}>
                        <Row><Col xs={12} >
                            <label><Message msgId="equalinterval.min"/></label>
                        </Col></Row>
                        <Row><Col xs={12} >
                            <NumberPicker
                                ref="min"
                                onChange={this.changeMin}
                                value={this.props.min}
                                format="-#,###.##"
                                precision={3}
                            />
                         {(this.props.error && this.props.error.type === 'min') ? this.renderErrorPopOver() : null}
                        </Col></Row>
                    </Col>
                    <Col xs={4}>
                        <Row><Col xs={12} >
                            <label><Message msgId="equalinterval.max"/></label>
                        </Col></Row>
                        <Row><Col xs={12} >
                            <NumberPicker
                                ref="max"
                                onChange={this.changeMax}
                                value={this.props.max}
                                format="-#,###.##"
                                precision={3}
                            />
                            {(this.props.error && this.props.error.type === 'max') ? this.renderErrorPopOver() : null}
                         </Col></Row>
                    </Col>
                    <Col xs={4}>
                        <Row>
                            <Col xs={12} >
                                <label><Message msgId="equalinterval.classes"/></label>
                            </Col>
                        </Row>
                        <Row>
                            <Col xs={12} >
                                <NumberPicker
                                    onChange={(number) => this.props.onChange("classes", number)}
                                    precision={0} min={3} max={12} step={1}
                                    value={this.props.classes}
                                />
                            </Col>
                        </Row>
                    </Col>
                    </Row>
                    <Row>
                    <Col xs={6} >
                        <Row><Col xs={12} >
                            <label><Message msgId="equalinterval.ramp"/></label>
                        </Col></Row>
                        <Row><Col xs={12} >
                            <Combobox data={this.getColorsSchema()}
                                groupBy="schema"
                                onChange={(value) => this.props.onChange("ramp", value.name)}
                                textField="name"
                                itemComponent={ColorRampItem} value={this.getRampValue()}/>
                        </Col></Row>
                    </Col>
                    <Col xs={6}>
                        <Row style={{paddingTop: "25px"}}>
                        <Col xs={12} >
                        <Button disabled={this.classifyDisabled()}
                                onClick={this.generateEqualIntervalRamp}
                                style={{"float": "right"}}>
                        <Message msgId="equalinterval.classify"/></Button>
                        </Col></Row>
                    </Col>
                </Row>
            </Grid>);
    },
    classifyDisabled() {
        return (this.props.error && this.props.error.type) ? true : false;
    },
    generateEqualIntervalRamp() {
        let ramp = colors[this.getRampValue()][this.props.classes];
        let min = this.props.min;
        let max = this.props.max;
        let step = (max - min) / this.props.classes;
        let colorRamp = ramp.map((color, idx) => {
            return {color: color, quantity: min + (idx * step)};
        });
        this.props.onClassify("colorRamp", colorRamp);
    },
    changeMin(value) {
        if (value < this.props.max) {
            if (this.props.error) {
                this.props.onChange("error", {});
            }
            this.props.onChange("min", value);
        } else {
            this.props.onChange("error", {
                type: "min",
                msg: "equalinterval.minerror"
            });
        }

    },
    changeMax(value) {
        if (value > this.props.min) {
            if (this.props.error) {
                this.props.onChange("error", {});
            }
            this.props.onChange("max", value);
        }else {
            this.props.onChange("error", {
                type: "max",
                msg: "equalinterval.maxerror"
            });
        }
    }
});

module.exports = EqualInterval;
