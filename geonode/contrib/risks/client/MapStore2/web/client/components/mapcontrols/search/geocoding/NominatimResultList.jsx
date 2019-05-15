/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var React = require('react');
var NominatimResult = require('./NominatimResult');
const mapUtils = require('../../../../utils/MapUtils');
const CoordinatesUtils = require('../../../../utils/CoordinatesUtils');
const I18N = require('../../../I18N/I18N');


let ResultList = React.createClass({
    propTypes: {
        results: React.PropTypes.array,
        mapConfig: React.PropTypes.object,
        onItemClick: React.PropTypes.func,
        addMarker: React.PropTypes.func,
        afterItemClick: React.PropTypes.func,
        notFoundMessage: React.PropTypes.oneOfType([React.PropTypes.object, React.PropTypes.string])
    },
    getDefaultProps() {
        return {
            onItemClick: () => {},
            addMarker: () => {},
            afterItemClick: () => {}
        };
    },
    onItemClick(item) {
        // coordinates from nominatim are minY minX maxY maxX   as strings
        var nBbox = item.boundingbox.map( (elem) => {return parseFloat(elem); });
        var bbox = [nBbox[2], nBbox[0], nBbox[3], nBbox[1]];
        // zoom by the max. extent defined in the map's config
        var mapSize = this.props.mapConfig.size;

        var newZoom = mapUtils.getZoomForExtent(CoordinatesUtils.reprojectBbox(bbox, "EPSG:4326", this.props.mapConfig.projection), mapSize, 0, 21, null);

        // center by the max. extent defined in the map's config
        var newCenter = mapUtils.getCenterForExtent(bbox, "EPSG:4326");

        this.props.onItemClick(newCenter, newZoom, {
            bounds: {
               minx: bbox[0],
               miny: bbox[1],
               maxx: bbox[2],
               maxy: bbox[3]
            },
            crs: "EPSG:4326",
             rotation: 0
         }, this.props.mapConfig.size, null, this.props.mapConfig.projection);
        this.props.addMarker({lat: newCenter.y, lng: newCenter.x});
        this.props.afterItemClick();
    },
    renderResults() {
        return this.props.results.map((item, idx)=> {return <NominatimResult key={item.osm_id || "res_" + idx} item={item} onItemClick={this.onItemClick}/>; });
    },
    render() {
        var notFoundMessage = this.props.notFoundMessage;
        if (!notFoundMessage) {
            notFoundMessage = <I18N.Message msgId="noresultfound" />;
        }
        if (!this.props.results) {
            return null;
        } else if (this.props.results.length === 0) {
            return <div className="search-result-list" style={{padding: "10px", textAlign: "center"}}>{notFoundMessage}</div>;
        }
        return (
            <div className="search-result-list">
                {this.renderResults()}
            </div>
        );
    },
    purgeResults() {

    }
});

module.exports = ResultList;
