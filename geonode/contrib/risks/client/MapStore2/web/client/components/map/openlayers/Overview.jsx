/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
/**
 * Available configuration params refer to http://openlayers.org/en/v3.10.1/apidoc/ol.control.OverviewMap.html#on
 *
 * collapsed   boolean | undefined experimental Whether the control should start collapsed or not (expanded). Default to true.
 * collapseLabel   string | Node | undefined   experimental Text label to use for the expanded overviewmap button. Default is «. Instead of text, also a Node (e.g. a span element) can be used.
 * collapsible boolean | undefined experimental Whether the control can be collapsed or not. Default to true.
 * label   string | Node | undefined   experimental Text label to use for the collapsed overviewmap button. Default is ». Instead of text, also a Node (e.g. a span element) can be used.
 * target  Element | undefined experimental Specify a target if you want the control to be rendered outside of the map's viewport.
 * tipLabel    string | undefined  experimental Text label to use for the button tip. Default is Overview map
 */


var React = require('react');
var ol = require('openlayers');
var Layers = require('../../../utils/openlayers/Layers');
var assign = require('object-assign');

require('./overview.css');

let Overview = React.createClass({
    propTypes: {
        id: React.PropTypes.string,
        map: React.PropTypes.object,
        overviewOpt: React.PropTypes.object,
        layers: React.PropTypes.array
    },
    getDefaultProps() {
        return {
          id: 'overview',
          overviewOpt: {},
          layers: [{type: 'osm', options: {}}]
        };
    },
    componentDidMount() {
        let olLayers = [];
        this.props.layers.forEach((layerOpt) => {
            olLayers.push(Layers.createLayer(layerOpt.type, layerOpt.options || {}));
        });
        let opt = assign({}, this.defaultOpt, this.props.overviewOpt, {layers: olLayers});
        this.overview = new ol.control.OverviewMap(opt);
        if (this.props.map) {
            this.overview.setMap(this.props.map);
        }
        this.box = this.overview.element.getElementsByClassName("ol-overviewmap-box").item(0);
        this.box.onmousedown = (e) => {
            this.dragstart(e);

            this.box.onmousemove = (ev) => {
                this.draggingel(ev);
            };
            this.overview.element.onmousemove = (ev) => {
                this.draggingel(ev);
            };
            this.box.onmouseup = () => {
                this.dragend();
                this.overview.element.onmousemove = null;
                this.box.onmousemove = null;
                this.box.onmouseup = null;
            };
        };
    },
    render() {
        return null;
    },
    dragstart(e) {
        if (!this.dragging) {
            this.dragBox = this.box.cloneNode();
            this.dragBox.setAttribute("class", "ol-overview-dargbox");
            this.dragBox.style.position = "relative";
            this.box.appendChild(this.dragBox);
            if (this.box.style.top === "") {
                this.offsetStartTop = 0;
            } else {
                this.offsetStartTop = parseInt(this.box.style.top.slice(0, -2), 10);
            }
            if (this.box.style.left === "") {
                this.offsetStartLeft = 0;
            } else {
                this.offsetStartLeft = parseInt(this.box.style.left.slice(0, -2), 10);
            }
            this.mouseStartTop = e.pageY;
            this.mouseStartLeft = e.pageX;
            this.dragging = true;
        }
    },
    draggingel(e) {
        if (this.dragging === true) {
            this.dragBox.style.top = (this.offsetStartTop + e.pageY - this.mouseStartTop) + 'px';
            this.dragBox.style.left = (this.offsetStartLeft + e.pageX - this.mouseStartLeft) + 'px';
            e.stopPropagation();
            e.preventDefault();
        }
    },
    dragend() {
        if (this.dragging === true) {
            let offset = {};
            offset.top = this.dragBox.style.top === "" ? 0 : parseInt(this.dragBox.style.top.slice(0, -2), 10);
            offset.left = this.dragBox.style.left === "" ? 0 : parseInt(this.dragBox.style.left.slice(0, -2), 10);
            this.box.removeChild(this.dragBox);
            delete this.dragBox;
            this.dragging = false;
            this.setNewExtent(offset);
        }
    },
    setNewExtent(offset) {
        let vWidth = this.box.offsetWidth;
        let vHeight = this.box.offsetHeight;
        let mapSize = this.props.map.getSize();
        let xMove = offset.left * (Math.abs(mapSize[0] / vWidth));
        let yMove = offset.top * (Math.abs(mapSize[1] / vHeight));
        let bottomLeft = [0 + xMove, mapSize[1] + yMove];
        let topRight = [mapSize[0] + xMove, 0 + yMove];
        let left = this.props.map.getCoordinateFromPixel(bottomLeft);
        let top = this.props.map.getCoordinateFromPixel(topRight);
        let extent = [left[0], left[1], top[0], top[1]];
        this.props.map.getView().fit(extent, mapSize, {nearest: true});
    },
    defaultOpt: {
        className: 'ol-overviewmap ol-custom-overviewmap',
        collapseLabel: '\u00BB',
        label: '\u00AB',
        collapsed: true,
        collapsible: true
    }

});

module.exports = Overview;
