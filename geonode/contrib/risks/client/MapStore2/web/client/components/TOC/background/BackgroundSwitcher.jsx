/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var {Grid, Col, Thumbnail, Glyphicon} = require('react-bootstrap');
var HYBRID = require('./images/mapthumbs/HYBRID.jpg');
var ROADMAP = require('./images/mapthumbs/ROADMAP.jpg');
var TERRAIN = require('./images/mapthumbs/TERRAIN.jpg');
var Aerial = require('./images/mapthumbs/Aerial.jpg');
var mapnik = require('./images/mapthumbs/mapnik.jpg');
var mapquestOsm = require('./images/mapthumbs/mapquest-osm.jpg');
var empty = require('./images/mapthumbs/none.jpg');
var unknown = require('./images/mapthumbs/dafault.jpg');
var Night2012 = require('./images/mapthumbs/NASA_NIGHT.jpg');
var AerialWithLabels = require('./images/mapthumbs/AerialWithLabels.jpg');
const OpenTopoMap = require('./images/mapthumbs/OpenTopoMap.jpg');
require("./style.css");

let thumbs = {
    google: {
        HYBRID,
        ROADMAP,
        TERRAIN
    },
    bing: {
        Aerial,
        AerialWithLabels
    },
    osm: {
        mapnik
    },
    mapquest: {
        osm: mapquestOsm
    },
    ol: {
        "undefined": empty
    },
    nasagibs: {
        Night2012
    },
    OpenTopoMap: {
        OpenTopoMap
    },
    unknown
};

let BackgroundSwitcher = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        name: React.PropTypes.oneOfType([React.PropTypes.string, React.PropTypes.element]),
        layers: React.PropTypes.array,
        columnProperties: React.PropTypes.object,
        propertiesChangeHandler: React.PropTypes.func,
        fluid: React.PropTypes.bool
    },
    getDefaultProps() {
        return {
            id: "background-switcher",
            icon: <Glyphicon glyph="globe"/>,
            fluid: true,
            columnProperties: {
                xs: 12,
                sm: 12,
                md: 12
             }
        };
    },
    renderBackgrounds() {
        if (!this.props.layers) {
            return <div></div>;
        }
        return this.renderLayers(this.props.layers);
    },
    renderLayers(layers) {
        let items = [];
        for (let i = 0; i < layers.length; i++) {
            let layer = layers[i];
            let thumb = thumbs[layer.source] && thumbs[layer.source][layer.name] || layer.thumbURL || thumbs.unknown;
            if (layer.invalid) {
                items.push(<Col {...this.props.columnProperties} key={i}>
              <Thumbnail data-position={i} key={"bkg-swicher-item-" + i} bsStyle="warning" src={thumb} alt={layer.source + " " + layer.name}>
                      <div style={{height: '38px', textOverflow: 'ellipsis', overflow: 'hidden'}}><strong>{layer.title}</strong></div>
              </Thumbnail>
          </Col>);
            } else {
                items.push(<Col {...this.props.columnProperties} key={i}>
              <Thumbnail data-position={i} key={"bkg-swicher-item-" + i} bsStyle={layer.visibility ? "primary" : "default"} src={thumb} alt={layer.source + " " + layer.name}
                  onClick={this.changeLayerVisibility}>
                      <div style={{height: '38px', textOverflow: 'ellipsis', overflow: 'hidden'}}><strong>{layer.title}</strong></div>
              </Thumbnail>
          </Col>);
            }

        }
        return items;
    },
    render() {
        return (
           <Grid id={this.props.id} className="BackgroundSwitcherComponent" fluid={this.props.fluid}>{this.renderBackgrounds()}</Grid>
        );
    },
    changeLayerVisibility(eventObj) {
        let position = parseInt(eventObj.currentTarget.dataset.position, 10);
        var layer = this.props.layers[position];
        this.props.propertiesChangeHandler(layer.id, {visibility: true});
    }
});

module.exports = BackgroundSwitcher;
