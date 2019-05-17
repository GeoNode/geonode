/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ConfigUtils = require('../../MapStore2/web/client/utils/ConfigUtils');
const ProxyUtils = require('../../MapStore2/web/client/utils/ProxyUtils');
const {isEqual} = require('lodash');
const html2canvas = require('html2canvas');
const canvg = require('canvg-browser');

const {Promise} = require('es6-promise');

require("../../MapStore2/web/client/components/map/leaflet/snapshot/snapshotMapStyle.css");
/**
 * GrabMap for Leaflet uses HTML2CANVAS to generate the image for the existing
 * leaflet map.
 * if it is not tainted, this can be used also to generate snapshot
 * (extracting the image URL from the canvas).
 */
let GrabLMap = React.createClass({
    propTypes: {
            config: ConfigUtils.PropTypes.config,
            layers: React.PropTypes.array,
            snapstate: React.PropTypes.object,
            active: React.PropTypes.bool,
            onSnapshotReady: React.PropTypes.func,
            onStatusChange: React.PropTypes.func,
            onSnapshotError: React.PropTypes.func,
            allowTaint: React.PropTypes.bool,
            browser: React.PropTypes.object,
            canvas: React.PropTypes.node,
            timeout: React.PropTypes.number,
            drawCanvas: React.PropTypes.bool,
            mapId: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            config: null,
            layers: [],
            snapstate: {state: "DISABLED"},
            active: false,
            onSnapshotReady: () => {},
            onStatusChange: () => {},
            onSnapshotError: () => {},
            browser: {},
            canvas: <canvas></canvas>,
            drawCanvas: true,
            mapId: "map",
            timeout: 1
        };
    },
    componentDidMount() {
        this.mapDiv = document.getElementById(this.props.mapId);
        this.proxy = null;
        let proxyUrl = ProxyUtils.getProxyUrl();
        if (proxyUrl) {
            if ( typeof proxyUrl === 'object') {
                proxyUrl = proxyUrl.url;
            }
            this.proxy = (proxyUrl.indexOf("?url=") !== -1) ? proxyUrl.replace("?url=", '') : proxyUrl;
        }
        // start SHOOTING
        let mapIsLoading = this.mapIsLoading(this.props.layers);
        if (!mapIsLoading && this.props.active) {
            this.props.onStatusChange("SHOTING");
            this.triggerShooting(this.props.timeout);
        }
    },
    componentWillReceiveProps(nextProps) {
        let mapIsLoading = this.mapIsLoading(nextProps.layers);
        let mapChanged = this.mapChanged(nextProps);
        if (this.previousTimeout) {
            clearTimeout(this.previousTimeout);
        }
        if ( nextProps.active && !mapIsLoading && mapChanged ) {
            this.props.onStatusChange("SHOTING");
        } else {
            if (!nextProps.active) {
                this.props.onStatusChange("DISABLED");
                if (this.props.snapstate.error) {
                    this.props.onSnapshotError(null);
                }
            }
        }
    },
    shouldComponentUpdate(nextProps) {
        return this.mapChanged(nextProps) || this.props.snapstate !== nextProps.snapstate;
    },
    componentDidUpdate(prevProps) {
        let mapIsLoading = this.mapIsLoading(this.props.layers);
        let mapChanged = this.mapChanged(prevProps);
        if ( this.props.active && !mapIsLoading && (mapChanged || this.props.snapstate.state === "SHOTING") ) {
            this.triggerShooting(this.props.timeout);
        }

    },
    componentWillUnmount() {
        if (this.previousTimeout) {
            clearTimeout(this.previousTimeout);
        }
    },
    getCanvas() {
        return this.refs.canvas;
    },
    render() {
        return (
            <canvas
                width={this.props.config && this.props.config.size ? this.props.config.size.width : "100%"}
                height={this.props.config && this.props.config.size ? this.props.config.size.height : "100%"}
                style={{
                    maxWidth: "500px",
                    maxHeight: "500px"
                }}
                ref="canvas" />
        );
    },
    mapChanged(nextProps) {
        return !isEqual(nextProps.layers, this.props.layers) || (nextProps.active !== this.props.active) || nextProps.config !== this.props.config;
    },
    mapIsLoading(layers) {
        return layers.some((layer) => { return layer.visibility && layer.loading; });
    },
    triggerShooting(delay) {
        if (this.previousTimeout) {
            clearTimeout(this.previousTimeout);
        }
        this.previousTimeout = setTimeout(() => {
            this.doSnapshot(this.props);
        },
        delay);
    },
    doSnapshot(props) {
        // get map style shifted
        const body = document.querySelector("body");
        body.scrollTop = 0;
        body.style.overflowY = 'hidden';
        let leftString = window.getComputedStyle(this.mapDiv).getPropertyValue("left");

        // get all the informations needed to snap svg before
        let mapPanes = this.mapDiv.getElementsByClassName("leaflet-map-pane");
        let mapPane = mapPanes && mapPanes[0];
        let objectPanes = mapPane && mapPane.getElementsByClassName("leaflet-objects-pane");
        let objectDiv = objectPanes && objectPanes[0];
        let svgs = objectDiv && objectDiv.getElementsByTagName("svg");
        let svg = svgs && svgs[0] && svgs[0].cloneNode(true);
        let svgOffsetX;
        let svgOffsetY;
        let svgH;
        let svgW;
        let svgString;
        if (svg && svg.outerHTML) {
            [svgOffsetX = 0, svgOffsetY = 0, svgW = 0, svgH = 0] = svg.getAttribute('viewBox').split(' ');
            svgString = svgs[0].outerHTML;
            svg.setAttribute("style", "");
        }
        let left = 0;
        if (leftString) {
            left = parseInt( leftString.replace('px', ''), 10);
        }

        // get pan position from translate 3d
        let leafletPane = this.mapDiv.getElementsByClassName("leaflet-map-pane");
        let panPosition = leafletPane && leafletPane[0] && leafletPane[0].style && leafletPane[0].style.transform ? leafletPane[0].style.transform.replace(/\(|\)|translate3d/g, '').split('px, ') : ['0', '0'];
        panPosition = [Number.parseFloat(panPosition[0]), Number.parseFloat(panPosition[1])];
        let tilePane = this.mapDiv.getElementsByClassName("leaflet-tile-pane");
        // clone to change style attributes
        let tilePaneClone = tilePane && tilePane[0].cloneNode(true);
        // bring back to hide
        tilePaneClone.style.zIndex = -9999;
        // append to prevent html2canvas errors
        document.body.appendChild(tilePaneClone);
        tilePaneClone.style.overflow = 'hidden';
        if (tilePaneClone) {
            let layers = [].slice.call(tilePaneClone.getElementsByClassName("leaflet-layer"), 0);
            layers.sort(function(a, b) {
                return Number.parseFloat(a.style.zIndex) - Number.parseFloat(b.style.zIndex);
            });
            let canvas = this.getCanvas();
            let context = canvas && canvas.getContext("2d");
            if (!context) {
                return;
            }
            context.clearRect(0, 0, canvas.width, canvas.height);
            // remove transform style from every tile images and add left top attributes
            let resetLayerStyles = function(l) {
                for (let i = 0; i < l.children.length; i++) {
                    if (l.children[i]) {
                        for (let j = 0; j < l.children[i].children.length; j++) {
                            if (l.children[i].children[j] && l.children[i].children[j].tagName === 'IMG') {
                                l.children[i].children[j].style.position = 'absolute';
                                l.children[i].children[j].style.left = l.children[i].children[j].getBoundingClientRect().left + left + panPosition[0] + 'px';
                                l.children[i].children[j].style.top = l.children[i].children[j].getBoundingClientRect().top + panPosition[1] + 'px';
                                l.children[i].children[j].style.transform = 'none';
                            }
                        }
                    }
                }
            };
            let queue = layers.map((l) => {
                let newCanvas = this.refs.canvas.cloneNode();
                newCanvas.width = newCanvas.width + left;
                resetLayerStyles(l);
                return html2canvas(l, {
                        // you have to provide a canvas to avoid html2canvas to crop the image
                        canvas: newCanvas,
                        logging: false,
                        proxy: this.proxy,
                        allowTaint: props && props.allowTaint,
                        // TODO: improve to useCORS if every source has CORS enabled
                        useCORS: true
                });
            }, this);
            queue = [this.refs.canvas, ...queue];
            // an issue in the html2canvas lib don't manage opacity correctly.
            // this is a workaround that apply the opacity on each layer snapshot,
            // then merges all the snapshots.
            Promise.all(queue).then((canvases) => {
                let finalCanvas = canvases.reduce((pCanv, canv, idx) => {
                    let l = layers[idx - 1];
                    if (l === undefined) {
                        return pCanv;
                    }
                    let cx = pCanv.getContext("2d");
                    if (l.style && !isNaN(Number.parseFloat(l.style.opacity))) {
                        cx.globalAlpha = Number.parseFloat(l.style.opacity);
                    }else {
                        cx.globalAlpha = 1;
                    }
                    cx.drawImage(canv, -1 * left, 0);
                    return pCanv;

                });
                let finialize = () => {
                    document.body.removeChild(tilePaneClone);
                    // TODO parse map-div transform to shift all markers toghether properly
                    let markers = this.mapDiv.getElementsByClassName("leaflet-marker-pane");
                    if ( markers && markers.length > 0) {
                        let newCanvas = this.refs.canvas.cloneNode();
                        newCanvas.width = newCanvas.width + left;
                        html2canvas(markers, {
                                // you have to provide a canvas to avoid html2canvas to crop the image
                                canvas: newCanvas,
                                logging: false,
                                proxy: this.proxy,
                                allowTaint: props && props.allowTaint,
                                // TODO: improve to useCORS if every source has CORS enabled
                                useCORS: props && props.allowTaint
                        }).then( (c) => {
                            let cx = finalCanvas.getContext("2d");
                            cx.globalAlpha = 1;
                            cx.drawImage(c, -1 * left, 0);
                            this.props.onStatusChange("READY", this.isTainted(finalCanvas));
                            this.props.onSnapshotReady(canvas, null, null, null, this.isTainted(finalCanvas));
                            body.style.overflowY = 'visible';
                        });
                    } else {
                        this.props.onStatusChange("READY", this.isTainted(finalCanvas));
                        this.props.onSnapshotReady(canvas, null, null, null, this.isTainted(finalCanvas));
                        body.style.overflowY = 'visible';
                    }
                };

                if (svg) {
                    let svgCanv = document.createElement('canvas');
                    svgOffsetX = svgOffsetX ? svgOffsetX : 0;
                    svgOffsetY = svgOffsetY ? svgOffsetY : 0;
                    svgCanv.setAttribute("width", Number.parseFloat(svgW) + left);
                    svgCanv.setAttribute("height", svgH);
                    canvg(svgCanv, svgString, {
                        ignoreMouse: true,
                        ignoreAnimation: true,
                        ignoreDimensions: true,
                        ignoreClear: true,
                        offsetX: svgOffsetX,
                        offsetY: svgOffsetY,
                        renderCallback: () => {
                            // window.open(svgCanv.toDataURL("image/png"), '_blank');
                            let ctx = finalCanvas.getContext('2d');
                            ctx.drawImage(svgCanv, -1 * left, -1);
                            finialize();
                        }
                    });
                } else {
                    finialize();
                }
            });
        }

    },
    /**
     * Check if the canvas is tainted, so if it is allowed to export images
     * from it.
     */
    isTainted(can) {
        let canvas = can || this.refs.canvas;
        let ctx = canvas.getContext("2d");
        try {
            // try to generate a small image
            ctx.getImageData(0, 0, 1, 1);
            return false;
        } catch(err) {
            // check the error code for tainted resources
            return (err.code === 18);
        }
    },
    exportImage() {
        return this.refs.canvas.toDataURL();
    }
});

module.exports = GrabLMap;
