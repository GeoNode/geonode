/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var React = require('react');
var Layers = require('../../../utils/cesium/Layers');
var assign = require('object-assign');

const CesiumLayer = React.createClass({
    propTypes: {
        map: React.PropTypes.object,
        type: React.PropTypes.string,
        options: React.PropTypes.object,
        position: React.PropTypes.number
    },
    componentDidMount() {
        this.createLayer(this.props.type, this.props.options, this.props.position, this.props.map);
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
            if (this.provider) {
                this.provider._position = newProps.position;
            }
        }
        if (this.props.options && this.props.options.params && this.layer.updateParams && newProps.options.visibility) {
            const changed = Object.keys(this.props.options.params).reduce((found, param) => {
                if (newProps.options.params[param] !== this.props.options.params[param]) {
                    return true;
                }
                return found;
            }, false);
            if (changed) {
                const oldProvider = this.provider;
                const newLayer = this.layer.updateParams(newProps.options.params);
                this.layer = newLayer;
                this.addLayer();
                setTimeout(() => {
                    this.removeLayer(oldProvider);
                }, 1000);

            }
        }
        this.updateLayer(newProps, this.props);
    },
    componentWillUnmount() {
        if (this.layer && this.props.map && !this.props.map.isDestroyed()) {
            if (this.layer.detached) {
                this.layer.remove();
            } else {
                if (this.layer.destroy) {
                    this.layer.destroy();
                }

                this.props.map.imageryLayers.remove(this.provider);
            }
        }
    },
    render() {
        if (this.props.children) {
            const layer = this.layer;
            const children = layer ? React.Children.map(this.props.children, child => {
                return child ? React.cloneElement(child, {container: layer, styleName: this.props.options && this.props.options.styleName}) : null;
            }) : null;
            return (
                <noscript>
                    {children}
                </noscript>
            );
        }
        return Layers.renderLayer(this.props.type, this.props.options, this.props.map, this.props.map.id, this.layer);

    },
    updateZIndex(position) {
        const layerPos = position || this.props.position;
        const actualPos = this.props.map.imageryLayers._layers.reduce((previous, current, index) => {
            return this.provider === current ? index : previous;
        }, -1);
        let newPos = this.props.map.imageryLayers._layers.reduce((previous, current, index) => {
            return (previous === -1 && layerPos < current._position) ? index : previous;
        }, -1);
        if (newPos === -1) {
            newPos = actualPos;
        }
        const diff = newPos - actualPos;
        if (diff !== 0) {
            Array.apply(null, {length: Math.abs(diff)}).map(Number.call, Number)
                .forEach(() => {
                    this.props.map.imageryLayers[diff > 0 ? 'raise' : 'lower'](this.provider);
                });
        }
    },
    setLayerVisibility(visibility) {
        var oldVisibility = this.props.options && this.props.options.visibility !== false;
        if (visibility !== oldVisibility) {
            if (visibility) {
                this.addLayer();
                this.updateZIndex();
            } else {
                this.removeLayer();
            }
        }
    },
    setLayerOpacity(opacity) {
        var oldOpacity = (this.props.options && this.props.options.opacity !== undefined) ? this.props.options.opacity : 1.0;
        if (opacity !== oldOpacity && this.layer && this.provider) {
            this.provider.alpha = opacity;
        }
    },
    createLayer(type, options, position, map) {
        if (type) {
            const opts = assign({}, options, position ? {zIndex: position} : null);
            this.layer = Layers.createLayer(type, opts, map);
            if (this.layer) {
                this.layer.layerName = options.name;
                this.layer.layerId = options.id;
            }
        }
    },
    updateLayer(newProps, oldProps) {
        const newLayer = Layers.updateLayer(newProps.type, this.layer, newProps.options, oldProps.options, this.props.map);
        if (newLayer) {
            this.layer = newLayer;
        }
    },
    addLayer() {
        if (this.layer && !this.layer.detached) {
            this.provider = this.props.map.imageryLayers.addImageryProvider(this.layer);
            this.provider._position = this.props.position;
            if (this.props.options.opacity) {
                this.provider.alpha = this.props.options.opacity;
            }
        }
    },
    removeLayer(provider) {
        const toRemove = provider || this.provider;
        if (toRemove) {
            this.props.map.imageryLayers.remove(toRemove);
        }
    }
});

module.exports = CesiumLayer;
