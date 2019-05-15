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
const MarkNameSelector = require('./MarkNameSelector');

const numberLocalizer = require('react-widgets/lib/localizers/simple-number');
numberLocalizer();
const {NumberPicker} = require('react-widgets');
require('react-widgets/lib/less/react-widgets.less');

const StylePoint = React.createClass({
    propTypes: {
        shapeStyle: React.PropTypes.object,
        setStyleParameter: React.PropTypes.func,
        showMarker: React.PropTypes.bool,
        showMarkSelector: React.PropTypes.bool
    },
    getDefaultProps() {
        return {
            shapeStyle: {},
            showMarker: true,
            showMarkSelector: false,
            setStyleParameter: () => {}
        };
    },
    render() {
        return (
            <Grid fluid={true}>
                <Row>
                    <Col xs={4} style={{padding: 0}}>
                        <StyleCanvas style={{ padding: 0, margin: "auto", display: "block"}}
                            height={97}
                            shapeStyle={this.props.shapeStyle}
                            geomType={this.props.shapeStyle.marker ? "Marker" : "Point"}
                        />
                    </Col>
                    <Col xs={7}>
                        {this.props.showMarker ? (<Row>
                            <Col xs={1}>
                                <input aria-label="..." type="checkbox" defaultChecked={this.props.shapeStyle.marker} onChange={(e) => { this.props.setStyleParameter("marker", e.target.checked); }}/>
                            </Col>
                            <Col style={{paddingLeft: 0, paddingTop: 1}} xs={4}>
                                <label>Marker</label>
                            </Col>
                        </Row>) : null}
                        {this.props.showMarkSelector ? (<Row style={{marginBottom: 4}}>
                            <Col style={{paddingTop: 7}}xs={4}><label>Mark</label></Col>
                            <Col xs={8} style={{paddingRight: 0, paddingLeft: 30}}>
                                <MarkNameSelector onChange={this.props.setStyleParameter} markName={this.props.shapeStyle.markName}/>
                            </Col>
                        </Row>) : null}
                        <Row >
                            <Col xs={4}>
                                <ColorPicker
                                    disabled={this.props.shapeStyle.marker}
                                    value={this.props.shapeStyle.color}
                                    line={false}
                                    text="Stroke"
                                    onChangeColor={(color) => {if (color) { this.props.setStyleParameter("color", color); } }} />
                            </Col>
                            <Col xs={8} style={{paddingRight: 0, paddingLeft: 30}}>
                                <NumberPicker disabled={this.props.shapeStyle.marker} onChange={(number) => {this.props.setStyleParameter("width", number); }} min={1} max={15} step={1} value={this.props.shapeStyle.width}/>
                            </Col>
                        </Row>
                        <Row style={{marginTop: 4}}>
                            <Col xs={4}>
                                <ColorPicker
                                    disabled={this.props.shapeStyle.marker}
                                    value={this.props.shapeStyle.fill}
                                    line={false}
                                    text="Fill"
                                    onChangeColor={(color) => { if (color) { this.props.setStyleParameter("fill", color); } }} />
                            </Col>
                            <Col xs={8} style={{paddingRight: 0, paddingLeft: 30}}>
                                <NumberPicker disabled={this.props.shapeStyle.marker} onChange={(number) => {this.props.setStyleParameter("radius", number); }} min={1} max={50} step={1} value={this.props.shapeStyle.radius}/>
                            </Col>
                        </Row>
                    </Col>
                </Row>
                </Grid>);
    }
});

module.exports = StylePoint;
