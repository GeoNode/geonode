/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const SharingLinks = require('./SharingLinks');
const Message = require('../I18N/Message');
const {Image, Panel, Button, Glyphicon} = require('react-bootstrap');
const {head} = require('lodash');
const assign = require('object-assign');
const {memoize} = require('lodash');

const CoordinatesUtils = require('../../utils/CoordinatesUtils');

const defaultThumb = require('./img/default.jpg');

const buildSRSMap = memoize((srs) => {
    return srs.reduce((previous, current) => {
        return assign(previous, {[current]: true});
    }, {});
});

const removeParameters = (url, skip) => {
    const urlparts = url.split('?');
    const params = {};
    if (urlparts.length >= 2 && urlparts[1]) {
        const pars = urlparts[1].split(/[&;]/g);
        pars.forEach((par) => {
            const param = par.split('=');
            if (skip.indexOf(param[0].toLowerCase()) === -1) {
                params[param[0]] = param[1];
            }
        });
    }
    return {url: urlparts[0], params};
};

require("./RecordItem.css");

const RecordItem = React.createClass({
    propTypes: {
        onLayerAdd: React.PropTypes.func,
        onZoomToExtent: React.PropTypes.func,
        record: React.PropTypes.object,
        buttonSize: React.PropTypes.string,
        onCopy: React.PropTypes.func,
        showGetCapLinks: React.PropTypes.bool,
        addAuthentication: React.PropTypes.bool,
        crs: React.PropTypes.string,
        onError: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            mapType: "leaflet",
            onLayerAdd: () => {},
            onZoomToExtent: () => {},
            onError: () => {},
            style: {},
            buttonSize: "small",
            onCopy: () => {},
            showGetCapLinks: false,
            crs: "EPSG:3857"
        };
    },
    getInitialState() {
        return {};
    },
    componentWillMount() {
        document.addEventListener('click', this.handleClick, false);
    },

    componentWillUnmount() {
        document.removeEventListener('click', this.handleClick, false);
    },
    getLinks(record) {
        let wmsGetCap = head(record.references.filter(reference => reference.type &&
            reference.type.indexOf("OGC:WMS") > -1 && reference.type.indexOf("http-get-capabilities") > -1));
        let wfsGetCap = head(record.references.filter(reference => reference.type &&
            reference.type.indexOf("OGC:WFS") > -1 && reference.type.indexOf("http-get-capabilities") > -1));
        let wmtsGetCap = head(record.references.filter(reference => reference.type &&
            reference.type.indexOf("OGC:WMTS") > -1 && reference.type.indexOf("http-get-capabilities") > -1));
        let links = [];
        if (wmsGetCap) {
            links.push({
                type: "WMS_GET_CAPABILITIES",
                url: wmsGetCap.url,
                labelId: 'catalog.wmsGetCapLink'
            });
        }
        if (wmtsGetCap) {
            links.push({
                type: "WMTS_GET_CAPABILITIES",
                url: wmtsGetCap.url,
                labelId: 'catalog.wmtsGetCapLink'
            });
        }
        if (wfsGetCap) {
            links.push({
                type: "WFS_GET_CAPABILITIES",
                url: wfsGetCap.url,
                labelId: 'catalog.wfsGetCapLink'
            });
        }
        return links;
    },
    renderThumb(thumbURL, record) {
        let thumbSrc = thumbURL || defaultThumb;

        return (<Image src={thumbSrc} alt={record && record.title} style={{
            "float": "left",
            width: "150px",
            maxHeight: "150px",
            marginRight: "20px"
        }}/>);

    },
    renderButtons(record) {
        if (!record || !record.references) {
            // we don't have a valid record so no buttons to add
            return null;
        }
        // let's extract the references we need
        let wms = head(record.references.filter(reference => reference.type && (reference.type === "OGC:WMS"
            || ((reference.type.indexOf("OGC:WMS") > -1 && reference.type.indexOf("http-get-map") > -1)))));
        let wmts = head(record.references.filter(reference => reference.type && (reference.type === "OGC:WMTS"
            || ((reference.type.indexOf("OGC:WMTS") > -1 && reference.type.indexOf("http-get-map") > -1)))));
        // let's create the buttons
        let buttons = [];
        if (wms) {
            buttons.push(
                <Button
                    key="wms-button"
                    className="record-button"
                    bsStyle="success"
                    bsSize={this.props.buttonSize}
                    onClick={() => { this.addLayer(wms); }}
                    key="addlayer">
                        <Glyphicon glyph="plus" />&nbsp;<Message msgId="catalog.addToMap"/>
                </Button>
            );
        }
        if (wmts) {
            buttons.push(
                <Button
                    key="wmts-button"
                    className="record-button"
                    bsStyle="success"
                    bsSize={this.props.buttonSize}
                    onClick={() => { this.addwmtsLayer(wmts); }}
                    key="addwmtsLayer">
                        <Glyphicon glyph="plus" />&nbsp;<Message msgId="catalog.addToMap"/>
                </Button>
            );
        }
        // creating get capbilities links that will be used to share layers info
        if (this.props.showGetCapLinks) {
            let links = this.getLinks(record);
            if (links.length > 0) {
                buttons.push(<SharingLinks key="sharing-links" popoverContainer={this} links={links}
                    onCopy={this.props.onCopy} buttonSize={this.props.buttonSize} addAuthentication={this.props.addAuthentication}/>);
            }
        }

        return (
            <div className="record-buttons">
                {buttons}
            </div>
        );
    },
    renderDescription(record) {
        if (!record) {
            return null;
        }
        if (typeof record.description === "string") {
            return record.description;
        } else if (Array.isArray(record.description)) {
            return record.description.join(", ");
        }
    },
    render() {
        let record = this.props.record;
        return (
            <Panel className="record-item">
                {this.renderThumb(record && record.thumbnail, record)}
                <div>
                    <h4>{record && record.title}</h4>
                    <h4><small>{record && record.identifier}</small></h4>
                    <p className="record-item-description">{this.renderDescription(record)}</p>
                </div>
                  {this.renderButtons(record)}
            </Panel>
        );
    },
    isLinkCopied(key) {
        return this.state[key];
    },
    setLinkCopiedStatus(key, status) {
        this.setState({[key]: status});
    },
    addLayer(wms) {
        const {url, params} = removeParameters(wms.url, ["request", "layer", "service", "version"]);
        const allowedSRS = buildSRSMap(wms.SRS);
        if (wms.SRS.length > 0 && !CoordinatesUtils.isAllowedSRS(this.props.crs, allowedSRS)) {
            this.props.onError('catalog.srs_not_allowed');
        } else {
            this.props.onLayerAdd({
                type: "wms",
                url: url,
                visibility: true,
                name: wms.params && wms.params.name,
                title: this.props.record.title || (wms.params && wms.params.name),
                bbox: {
                    crs: this.props.record.boundingBox.crs,
                    bounds: {
                        minx: this.props.record.boundingBox.extent[0],
                        miny: this.props.record.boundingBox.extent[1],
                        maxx: this.props.record.boundingBox.extent[2],
                        maxy: this.props.record.boundingBox.extent[3]
                    }
                },
                links: this.getLinks(this.props.record),
                params: params,
                allowedSRS: allowedSRS
            });
            if (this.props.record.boundingBox) {
                let extent = this.props.record.boundingBox.extent;
                let crs = this.props.record.boundingBox.crs;
                this.props.onZoomToExtent(extent, crs);
            }
        }
    },
    addwmtsLayer(wmts) {
        const {url, params} = removeParameters(wmts.url, ["request", "layer"]);
        const allowedSRS = buildSRSMap(wmts.SRS);
        if (wmts.SRS.length > 0 && !CoordinatesUtils.isAllowedSRS(this.props.crs, allowedSRS)) {
            this.props.onError('catalog.srs_not_allowed');
        } else {
            this.props.onLayerAdd({
                type: "wmts",
                url: url,
                visibility: true,
                name: wmts.params && wmts.params.name,
                title: this.props.record.title || (wmts.params && wmts.params.name),
                matrixIds: this.props.record.matrixIds || [],
                tileMatrixSet: this.props.record.tileMatrixSet || [],
                bbox: {
                    crs: this.props.record.boundingBox.crs,
                    bounds: {
                        minx: this.props.record.boundingBox.extent[0],
                        miny: this.props.record.boundingBox.extent[1],
                        maxx: this.props.record.boundingBox.extent[2],
                        maxy: this.props.record.boundingBox.extent[3]
                    }
                },
                links: this.getLinks(this.props.record),
                params: params,
                allowedSRS: allowedSRS
            });
            if (this.props.record.boundingBox) {
                let extent = this.props.record.boundingBox.extent;
                let crs = this.props.record.boundingBox.crs;
                this.props.onZoomToExtent(extent, crs);
            }
        }
    }
});

module.exports = RecordItem;
