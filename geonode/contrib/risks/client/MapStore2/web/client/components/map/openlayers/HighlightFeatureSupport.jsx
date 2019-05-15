/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const ol = require('openlayers');

const HighlightFeatureSupport = React.createClass({
    propTypes: {
        map: React.PropTypes.object,
        layer: React.PropTypes.string.isRequired,
        status: React.PropTypes.oneOf(['disabled', 'enabled', 'update']),
        updateHighlighted: React.PropTypes.func,
        selectedStyle: React.PropTypes.object,
        features: React.PropTypes.array
    },
    contextTypes: {
        messages: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            status: 'disabled',
            updateHighlighted: () => {},
            selectedStyle: {
                    "type": "Point",
                    "radius": 12,
                    "stroke": {
                        "width": 4,
                        "color": "yellow"
                    },
                    "fill": {
                        "color": "red"
                    }
            }
        };
    },
    componentDidMount() {

        this.createSelectInteraction();
        if (this.props.status === 'enabled') {
            this._selectInteraction.setActive(true);
        }else {
            this._selectInteraction.setActive(false);
        }
        if (this.props.features) {
            this.highlightFeatures(this.props.features);
        }
    },
    shouldComponentUpdate(nx) {
        let pr = this.props;
        return nx.status !== pr.status ||
            nx.layer !== pr.layer ||
            (nx.status === 'update' &&
             nx.features.toString() !== pr.features.toString());
    },
    componentWillUpdate(np) {
        switch (np.status) {
            case "enabled": {
                this.setSelectInteraction(np);
                break;
            }
            case "disabled": {
                this.cleanSupport();
                break;
            }
            case "update": {
                this.highlightFeatures(np.features);
                break;
            }
            default:
                return;
        }
    },
    componentWillUnmount() {
        if (this._selectInteraction) {
            this.cleanSupport();
            this._selectInteraction.un('select', this.selectionChange, this);
            this.props.map.removeInteraction(this._selectInteraction);
            this._selectInteraction = null;
            this._style = null;
        }
    },
    getLayer() {
        let layer;
        this.props.map.getLayers().forEach((l) => {
            if (this.layersFilter(l)) {
                layer = l;
            }
        }, this);
        return layer;
    },
    render() {
        return null;
    },
    setSelectInteraction() {
        if (!this._selectInteraction.getActive()) {
            this._selectInteraction.setActive(true);
        }
    },
    createSelectInteraction() {
        this.createStyle();
        this._selectInteraction = new ol.interaction.Select({
            layers: this.layersFilter,
            style: this._style,
            toggleCondition: ol.events.condition.platformModifierKeyOnly
            });
        this._selectInteraction.on('select', this.selectionChange, this);
        this.props.map.addInteraction(this._selectInteraction);
    },
    selectionChange() {
        let newHighlighted = [];
        this._selectInteraction.getFeatures().forEach((f) => { newHighlighted.push(f.getId()); });
        this.props.updateHighlighted(newHighlighted, "");
    },
    cleanSupport() {
        if (this._selectInteraction && this._selectInteraction.getActive()) {
            this._selectInteraction.getFeatures().clear();
            this.props.updateHighlighted([], "");
            this._selectInteraction.setActive(false);
        }

    },
    layersFilter(l) {
        return this.props.layer && l.get('msId') === this.props.layer;
    },
    createStyle() {
        let sty = this.props.selectedStyle;
        let style = {
            stroke: new ol.style.Stroke( sty.stroke ? sty.stroke : {
                    color: 'blue',
                    width: 1
                }),
                fill: new ol.style.Fill(sty.fill ? sty.fill : {
                    color: 'blue'
                })
            };
        if (sty.type === "Point") {
            style = {
                    image: new ol.style.Circle({...style, radius: sty.radius || 5})
                };
        }
        this._style = new ol.style.Style(style);
    },
    highlightFeatures(features) {
        let layer = this.getLayer();
        let ftColl = this._selectInteraction.getFeatures();
        ftColl.clear();
        if (layer) {
            let ft = layer.getSource().getFeatures();
            ft.map((f)=> {
                if (features.indexOf(f.getId()) !== -1) {
                    ftColl.push(f);
                }
            }, this);
        }
    }
});

module.exports = HighlightFeatureSupport;
