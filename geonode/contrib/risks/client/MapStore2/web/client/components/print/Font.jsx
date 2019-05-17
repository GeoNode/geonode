/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const Choice = require('./Choice');
const {Grid, Row, Col, FormControl, Button, Glyphicon} = require('react-bootstrap');

const Font = React.createClass({
    propTypes: {
        fonts: React.PropTypes.array,
        label: React.PropTypes.string,
        onChangeFamily: React.PropTypes.func,
        onChangeSize: React.PropTypes.func,
        onChangeBold: React.PropTypes.func,
        onChangeItalic: React.PropTypes.func,
        family: React.PropTypes.string,
        size: React.PropTypes.number,
        bold: React.PropTypes.bool,
        italic: React.PropTypes.bool
    },
    getDefaultProps() {
        return {
            fonts: ['Verdana', 'Serif', 'SansSerif', 'Arial', 'Courier New', 'Tahoma', 'Times New Roman'],
            label: 'Font',
            onChangeFamily: () => {},
            onChangeSize: () => {},
            family: '',
            size: 8,
            bold: false,
            italic: false
        };
    },
    onChangeFamily(family) {
        this.props.onChangeFamily(family);
    },
    onChangeSize(size) {
        this.props.onChangeSize(size);
    },
    render() {
        return (
            <Grid fluid>
                <Row>
                    <Col xs={12}>
                        <label className="control-label">{this.props.label}</label>
                    </Col>
                </Row>
                <Row>
                    <Col xs={5}>
                        <Choice ref="family" onChange={this.onChangeFamily} label="" items={this.props.fonts.map((font) => ({name: font, value: font}))}
                            selected={this.props.family}/>
                    </Col>
                    <Col xs={3}>
                        <FormControl ref="size" type="number" value={this.props.size} onChange={this.onChangeSize}/>
                    </Col>
                    <Col xs={2}>
                        <Button bsStyle="primary" bsSize="small" active={this.props.bold} onClick={this.toggleBold}><Glyphicon glyph="bold"/></Button>
                    </Col>
                    <Col xs={2}>
                        <Button bsStyle="primary" bsSize="small" active={this.props.italic} onClick={this.toggleItalic}><Glyphicon glyph="italic"/></Button>
                    </Col>
                </Row>
            </Grid>
        );
    },
    toggleBold() {
        this.props.onChangeBold(!this.props.bold);
    },
    toggleItalic() {
        this.props.onChangeItalic(!this.props.italic);
    }
});

module.exports = Font;
