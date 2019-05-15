/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {Grid, Row, Col} = require('react-bootstrap');
const ColorPicker = require('./ColorPicker');
const StyleCanvas = require('./StyleCanvas');
const numberLocalizer = require('react-widgets/lib/localizers/simple-number');
numberLocalizer();
const {NumberPicker} = require('react-widgets');
require('react-widgets/lib/less/react-widgets.less');

const StylePolygon = React.createClass({
    propTypes: {
        shapeStyle: React.PropTypes.object,
        setStyleParameter: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            shapeStyle: {},
            setStyleParameter: () => {}
        };
    },
    render() {
        return (<Grid fluid={true}>
                <Row>
                    <Col xs={4} style={{padding: 0}}>
                        <StyleCanvas style={{ padding: 0, margin: "auto", display: "block"}}
                            shapeStyle={this.props.shapeStyle}
                            geomType="Polygon"
                        />
                    </Col>
                    <Col xs={7}>
                        <Row style={{marginTop: 7}}>
                            <Col xs={4}>
                                <ColorPicker
                                    value={this.props.shapeStyle.color}
                                    line={false}
                                    text="Stroke"
                                    onChangeColor={(color) => {if (color) { this.props.setStyleParameter("color", color); } }} />
                            </Col>
                            <Col xs={8} style={{paddingRight: 0, paddingLeft: 30}}>
                                <NumberPicker onChange={(number) => {this.props.setStyleParameter("width", number); }} min={1} max={15} step={1} value={this.props.shapeStyle.width}/>
                            </Col>
                        </Row>
                        <Row style={{marginTop: 4}}>
                            <Col xs={6}>
                                <ColorPicker
                                    value={this.props.shapeStyle.fill}
                                    line={false}
                                    text="Fill"
                                    onChangeColor={(color) => { if (color) { this.props.setStyleParameter("fill", color); } }} />
                            </Col>

                        </Row>
                    </Col>
                </Row>
                </Grid>);
    }
});

module.exports = StylePolygon;
