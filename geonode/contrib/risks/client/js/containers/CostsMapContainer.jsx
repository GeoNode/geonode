/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {connect} = require('react-redux');
const {findIndex} = require('lodash');
const {loadMapConfig} = require('../../MapStore2/web/client/actions/config');
const {disasterRiskLayerSelector} = require('../../MapStore2/web/client/selectors/layers');
const MapViewer = connect(() => ({}), {
    loadMapConfig: loadMapConfig.bind(null, "/static/js/config-costs.json")
})(require('../../MapStore2/web/client/containers/MapViewer'));
const Legend = connect(disasterRiskLayerSelector)(require('../../MapStore2/web/client/components/TOC/fragments/legend/Legend'));
// const {sliderSelector} = require('../selectors/disaster');
// const {setDimIdx, chartSliderUpdate, getSFurtherResourceData} = require('../actions/disaster');
const {setControlProperty, toggleControl} = require('../../MapStore2/web/client/actions/controls');
// const {show, hide} = require('react-notification-system-redux');
const LayerBtn = connect((state) => {return {enabled: state.controls && state.controls.toolbar && state.controls.toolbar.active }; }, {toggleTOC: setControlProperty.bind(null, "toolbar", "active", "toc", true)})(require('../components/LayerBtn'));
const IdentifyBtn = connect((state) => ({
        active: state.controls && state.controls.info && state.controls.info.enabled,
        enabled: findIndex(state.layers.flat, l => l.id === '_riskAn_') !== -1 ? true : false }), {toggleTOC: toggleControl.bind(null, "info", "enabled")})(require('../components/IdentifyBtn'));
// const ExtendedSlider = connect(sliderSelector, {setDimIdx, chartSliderUpdate, show, hide, getData: getSFurtherResourceData })(require('../components/ExtendedSlider'));
const FurtherResources = connect(({disaster} = {}) => ({
    analysisType: disaster.riskAnalysis && disaster.riskAnalysis.furtherResources && disaster.riskAnalysis.furtherResources.analysisType || [],
    hazardType: disaster.riskAnalysis && disaster.riskAnalysis.furtherResources && disaster.riskAnalysis.furtherResources.hazardType || []
}))(require('../components/FurtherResources'));
const MapContainer = (props) => (
        <div className="col-sm-5">
            <div id="disaster-map-main-container" className="disaster-map-container">
                <div className="container-fluid">
                    <div id="disaster-map-tools" className="btn-group pull-left disaster-map-tools"><LayerBtn/><IdentifyBtn/></div>
                </div>
                <div className="drc">
                    <div className="drc-map-container">
                        <MapViewer plugins={props.plugins} params={{mapType: "leaflet"}}/>
                    </div>
                </div>
                <div className="container-fluid">
                    {/*<div id="disaster-map-slider" className="row">
                        <ExtendedSlider uid={'map_slider'} dimIdx={'dim2Idx'} color={'#333'}/>
                    </div>*/}
                    <div id="disaster-map-legend" className="row">
                        <Legend/>
                    </div>
                </div>
            </div>
            <FurtherResources/>
        </div>
);

module.exports = MapContainer;
