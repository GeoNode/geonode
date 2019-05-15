/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Grid, Row, Col, Button} = require('react-bootstrap');

const Combobox = require('react-widgets').Combobox;

const ColorMapGrid = require('./ColorMapGrid');

const Message = require('../I18N/Message');

const PseudoColorSettings = React.createClass({
    propTypes: {
        type: React.PropTypes.oneOf(['ramp', 'intervals', 'values']),
        opacity: React.PropTypes.oneOfType([React.PropTypes.number, React.PropTypes.string]),
        selected: React.PropTypes.number,
        colorMapEntry: React.PropTypes.array,
        onChange: React.PropTypes.func,
        extended: React.PropTypes.bool
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            type: 'ramp',
            opacity: "1",
            selected: null,
            colorMapEntry: [],
            onChange: () => {},
            extended: false
        };
    },
    render() {
        return (
            <Grid fluid>
                <Row>
                    <Col xs={3} >
                        <Row>
                            <label><Message msgId="pseudocolorsettings.type"/></label>
                        </Row>
                        <Row>
                            <Combobox
                                data={['ramp', 'intervals', 'values']}
                                value={this.props.type}
                                onChange={(v) => this.props.onChange("type", v)} />
                        </Row>
                        <Row style={{paddingTop: 8}}>
                        <label><Message msgId="pseudocolorsettings.extended"/></label>&nbsp;&nbsp;<input type="checkbox" onChange={(e) => this.props.onChange("extended", e.target.checked)} checked={this.props.extended} />
                        </Row>
                        </Col>
                        <Col xsOffset={1} xs={8}>
                            <Row> <label><Message msgId="pseudocolorsettings.colormap"/></label></Row>
                            <Row style={{marginBottom: "10px"}}>
                                <ColorMapGrid
                                    selectEntry={this.selectEntry}
                                    valueChanged={(colorMap) => this.props.onChange("colorMapEntry", colorMap)}
                                    entries={this.props.colorMapEntry}/>
                            </Row>
                        </Col>
                    </Row>
                    <Row>
                        <Col xs={4} xsOffset={4} style={{padding: "0px" }}>
                            <Button onClick={this.addEntry}>
                            <Message msgId="pseudocolorsettings.add"/></Button>
                        </Col>
                        <Col xs={4} style={{padding: "0px" }}>
                            <Button disabled={(this.props.selected === null) ? true : false }
                            onClick={this.removeEntry} style={{"float": "right"}}>
                            <Message msgId="pseudocolorsettings.remove"/></Button>
                        </Col>
                    </Row>
              </Grid>
            );
    },
    addEntry() {
        let colorMapEntry = (this.props.colorMapEntry) ? this.props.colorMapEntry.slice() : [];
        let quantity = (colorMapEntry.length > 0) ? colorMapEntry[colorMapEntry.length - 1].quantity + 0.01 : 0;
        let label = (quantity.toFixed) ? quantity.toFixed(2) : quantity;
        colorMapEntry.push({color: '#AA34FF', quantity: quantity, label: label });
        this.props.onChange("colorMapEntry", colorMapEntry);
    },
    removeEntry() {
        let colorMapEntry = this.props.colorMapEntry.filter((e, idx) => {
            return idx !== this.props.selected;
        });
        this.props.onChange("selected", null);
        this.props.onChange("colorMapEntry", colorMapEntry);
    },
    selectEntry(id) {
        if ( id !== this.props.selected) {
            this.props.onChange("selected", id);
        }
    }


});

module.exports = PseudoColorSettings;
