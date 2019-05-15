/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');

const Message = require('../../components/I18N/Message');
const LayersUtils = require('../../utils/LayersUtils');
const LocaleUtils = require('../../utils/LocaleUtils');
const FileUtils = require('../../utils/FileUtils');
let StyleUtils;
const {Grid, Row, Col, Button} = require('react-bootstrap');

const Combobox = require('react-widgets').DropdownList;

const SelectShape = require('./SelectShape');

const {Promise} = require('es6-promise');

const ShapeFileUploadAndStyle = React.createClass({
    propTypes: {
        bbox: React.PropTypes.array,
        layers: React.PropTypes.array,
        selected: React.PropTypes.object,
        style: React.PropTypes.object,
        shapeStyle: React.PropTypes.object,
        onShapeError: React.PropTypes.func,
        onShapeSuccess: React.PropTypes.func,
        onShapeChoosen: React.PropTypes.func,
        addShapeLayer: React.PropTypes.func,
        shapeLoading: React.PropTypes.func,
        onSelectLayer: React.PropTypes.func,
        onLayerAdded: React.PropTypes.func,
        onZoomSelected: React.PropTypes.func,
        updateShapeBBox: React.PropTypes.func,
        error: React.PropTypes.string,
        success: React.PropTypes.string,
        mapType: React.PropTypes.string,
        buttonSize: React.PropTypes.string,
        uploadMessage: React.PropTypes.object,
        cancelMessage: React.PropTypes.object,
        addMessage: React.PropTypes.object,
        stylers: React.PropTypes.object,
        uploadOptions: React.PropTypes.object,
        createId: React.PropTypes.func
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            mapType: "leaflet",
            buttonSize: "small",
            uploadOptions: {},
            createId: () => undefined,
            bbox: null
        };
    },
    componentWillMount() {
        StyleUtils = require('../../utils/StyleUtils')(this.props.mapType);
    },
    getInitialState() {
        return {
            useDefaultStyle: false,
            zoomOnShapefiles: true
        };
    },
    getGeomType(layer) {
        if (layer && layer.features && layer.features[0].geometry) {
            return layer.features[0].geometry.type;
        }
    },
    renderError() {
        return (<Row>
                   <div style={{textAlign: "center"}} className="alert alert-danger">{this.props.error}</div>
                </Row>);
    },
    renderSuccess() {
        return (<Row>
                   <div style={{textAlign: "center", overflowWrap: "break-word"}} className="alert alert-success">{this.props.success}</div>
                </Row>);
    },
    renderStyle() {
        return this.props.stylers[this.getGeomType(this.props.selected)];
    },
    renderDefaultStyle() {
        return (this.props.selected) ? (
            <Row>
                <Col xs={2}>
                    <input aria-label="..." type="checkbox" defaultChecked={this.state.useDefaultStyle} onChange={(e) => {this.setState({useDefaultStyle: e.target.checked}); }}/>
                </Col>
                <Col style={{paddingLeft: 0, paddingTop: 1}} xs={10}>
                    <label><Message msgId="shapefile.defaultStyle"/></label>
                </Col>

                <Col xs={2}>
                    <input aria-label="..." type="checkbox" defaultChecked={this.state.zoomOnShapefiles} onChange={(e) => {this.setState({zoomOnShapefiles: e.target.checked}); }}/>
                </Col>
                <Col style={{paddingLeft: 0, paddingTop: 1}} xs={10}>
                    <label><Message msgId="shapefile.zoom"/></label>
                </Col>
            </Row>
        ) : null;
    },
    render() {
        return (
            <Grid role="body" style={{width: "300px"}} fluid>
                {(this.props.error) ? this.renderError() : null}
                {(this.props.success) ? this.renderSuccess() : null}
            <Row style={{textAlign: "center"}}>
                {
            (this.props.selected) ?
                <Combobox data={this.props.layers} value={this.props.selected} onSelect={(value)=> this.props.onSelectLayer(value)} valueField={"id"} textField={"name"} /> :
                <SelectShape {...this.props.uploadOptions} errorMessage="shapefile.error.select" text={this.props.uploadMessage} onShapeChoosen={this.addShape} onShapeError={this.props.onShapeError}/>
            }
            </Row>
            <Row style={{marginBottom: 10}}>
                {(this.state.useDefaultStyle) ? null : this.renderStyle()}
            </Row>
            {this.renderDefaultStyle()}

                {(this.props.selected) ?
                (<Row>
                    <Col xsOffset={6} xs={3}> <Button bsSize={this.props.buttonSize} disabled={!this.props.selected} onClick={() => {this.props.onShapeChoosen(null); }}>{this.props.cancelMessage}</Button></Col>
                    <Col xs={3}> <Button bsStyle="primary" bsSize={this.props.buttonSize} disabled={!this.props.selected} onClick={this.addToMap}>{this.props.addMessage}</Button></Col>
                </Row>
                    ) : null }
            </Grid>
        );
    },
    addShape(files) {
        this.props.shapeLoading(true);
        let queue = files.map((file) => {
            return FileUtils.readZip(file).then((buffer) => {
                return FileUtils.shpToGeoJSON(buffer);
            });
        }, this);
        Promise.all(queue).then((geoJsons) => {
            let ls = geoJsons.reduce((layers, geoJson) => {
                if (geoJson) {
                    return layers.concat(geoJson.map((layer) => {
                        return LayersUtils.geoJSONToLayer(layer, this.props.createId(layer, geoJson));
                    }));
                }
            }, []);
            this.props.onShapeChoosen(ls);
            this.props.shapeLoading(false);
        }).catch((e) => {
            this.props.shapeLoading(false);
            this.props.onShapeError(e.message || e);
        });
    },
    addToMap() {
        this.props.shapeLoading(true);
        let styledLayer = this.props.selected;
        if (!this.state.useDefaultStyle) {
            styledLayer = StyleUtils.toVectorStyle(styledLayer, this.props.shapeStyle);
        }
        Promise.resolve(this.props.addShapeLayer( styledLayer )).then(() => {
            this.props.shapeLoading(false);

            // calculates the bbox that contains all shapefiles added
            const bbox = this.props.layers[0].features.reduce((bboxtotal, feature) => {
                if (feature.geometry.bbox && feature.geometry.bbox[0] && feature.geometry.bbox[1] && feature.geometry.bbox[2] && feature.geometry.bbox[3] ) {
                    return [
                        Math.min(bboxtotal[0], feature.geometry.bbox[0]),
                        Math.min(bboxtotal[1], feature.geometry.bbox[1]),
                        Math.max(bboxtotal[2], feature.geometry.bbox[2]),
                        Math.max(bboxtotal[3], feature.geometry.bbox[3])
                    ] || bboxtotal;
                } else if (feature.geometry && feature.geometry.type === "Point" && feature.geometry.coordinates && feature.geometry.coordinates.length >= 2) {
                    return [Math.min(bboxtotal[0], feature.geometry.coordinates[0]),
                        Math.min(bboxtotal[1], feature.geometry.coordinates[1]),
                        Math.max(bboxtotal[2], feature.geometry.coordinates[0]),
                        Math.max(bboxtotal[3], feature.geometry.coordinates[1])
                    ];
                }
                return bboxtotal;
            }, this.props.bbox);
            if (this.state.zoomOnShapefiles) {
                this.props.updateShapeBBox(bbox);
                this.props.onZoomSelected(bbox, "EPSG:4326");
            }
            this.props.onShapeSuccess(this.props.layers[0].name + LocaleUtils.getMessageById(this.context.messages, "shapefile.success"));
            this.props.onLayerAdded(this.props.selected);
        }).catch((e) => {
            this.props.shapeLoading(false);
            this.props.onShapeError(e.message || e);
        });
    }
});


module.exports = ShapeFileUploadAndStyle;
