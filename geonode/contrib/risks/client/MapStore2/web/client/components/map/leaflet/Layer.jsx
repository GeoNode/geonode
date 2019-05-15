/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var Layers = require('../../../utils/leaflet/Layers');
var assign = require('object-assign');
var {isEqual} = require('lodash');

const LeafletLayer = React.createClass({
    propTypes: {
        map: React.PropTypes.object,
        type: React.PropTypes.string,
        srs: React.PropTypes.string,
        options: React.PropTypes.object,
        position: React.PropTypes.number,
        zoomOffset: React.PropTypes.number,
        onInvalid: React.PropTypes.func,
        onClick: React.PropTypes.func
    },
    getDefaultProps() {
        return {
            onInvalid: () => {}
        };
    },
    componentDidMount() {
        this.valid = true;
        this.createLayer(this.props.type, this.props.options, this.props.position);
        if (this.props.options && this.layer && this.props.options.visibility !== false) {
            this.addLayer();
            this.updateZIndex();
        }
    },
    componentWillReceiveProps(newProps) {
        const newVisibility = newProps.options && newProps.options.visibility !== false;
        this.setLayerVisibility(newVisibility);

        const newOpacity = (newProps.options && newProps.options.opacity !== undefined) ? newProps.options.opacity : 1.0;
        this.setLayerOpacity(newOpacity);

        if (newProps.position !== this.props.position) {
            this.updateZIndex(newProps.position);
        }
        this.updateLayer(newProps, this.props);
    },
    shouldComponentUpdate(newProps) {
        // the reduce returns true when a prop is changed
        // optimizing when options are equal ignorning loading key
        return !(["map", "type", "srs", "position", "zoomOffset", "onInvalid", "onClick", "options", "children"].reduce( (prev, p) => {
            switch (p) {
                case "map":
                case "type":
                case "srs":
                case "position":
                case "zoomOffset":
                case "onInvalid":
                case "onClick":
                case "children":
                    return prev && this.props[p] === newProps[p];
                case "options":
                    return prev && (this.props[p] === newProps[p] || isEqual({...this.props[p], loading: false}, {...newProps[p], loading: false}));
                default:
                    return prev;
            }
        }, true));
    },
    componentWillUnmount() {
        if (this.layer && this.props.map) {
            this.removeLayer();
        }
    },
    render() {
        if (this.props.children) {
            const layer = this.layer;
            const children = layer ? React.Children.map(this.props.children, child => {
                return child ? React.cloneElement(child, {container: layer, styleName: this.props.options && this.props.options.styleName, onClick: this.props.onClick}) : null;
            }) : null;
            return (
                <noscript>
                    {children}
                </noscript>
            );
        }
        return Layers.renderLayer(this.props.type, this.props.options, this.props.map, this.props.map.id, this.layer);

    },
    setLayerVisibility(visibility) {
        var oldVisibility = this.props.options && this.props.options.visibility !== false;
        if (visibility !== oldVisibility) {
            if (visibility) {
                this.addLayer();
            } else {
                this.removeLayer();
            }
            this.updateZIndex();

        }
    },
    setLayerOpacity(opacity) {
        var oldOpacity = (this.props.options && this.props.options.opacity !== undefined) ? this.props.options.opacity : 1.0;
        if (opacity !== oldOpacity && this.layer && this.layer.setOpacity) {
            this.layer.setOpacity(opacity);
        }
    },
    generateOpts(options, position) {
        return assign({}, options, position ? {zIndex: position, srs: this.props.srs } : null, {
            zoomOffset: -this.props.zoomOffset,
            onError: () => {
                this.props.onInvalid(this.props.type, this.props.options);
            }
        });
    },
    updateZIndex(position) {
        let newPosition = position || this.props.position;
        if (newPosition && this.layer && this.layer.setZIndex) {
            this.layer.setZIndex(newPosition);
        }
    },
    createLayer(type, options, position) {
        if (type) {
            const opts = this.generateOpts(options, position);
            this.layer = Layers.createLayer(type, opts);
            if (this.layer) {
                this.layer.layerName = options.name;
                this.layer.layerId = options.id;
            }
            this.forceUpdate();
        }
    },
    updateLayer(newProps, oldProps) {
        Layers.updateLayer(newProps.type, this.layer, this.generateOpts(newProps.options, newProps.position), this.generateOpts(oldProps.options, oldProps.position));
    },
    addLayer() {
        if (this.isValid()) {
            this.props.map.addLayer(this.layer);
        }
    },
    removeLayer() {
        if (this.isValid()) {
            this.props.map.removeLayer(this.layer);
        }
    },
    isValid() {
        if (this.layer) {
            const valid = Layers.isValid(this.props.type, this.layer);
            if (this.valid && !valid) {
                this.props.onInvalid(this.props.type, this.props.options);
            }
            this.valid = valid;
            return valid;
        }
        return false;
    }
});

module.exports = LeafletLayer;
