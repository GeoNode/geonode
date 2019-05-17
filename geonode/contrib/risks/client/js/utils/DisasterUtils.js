/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {isString} = require('lodash');
const assign = require('object-assign');
function configLayer(baseurl, layerName, layerId, layerTitle, visibility = true, group) {
    return assign({
    "id": layerId,
    "type": "wms",
    "url": baseurl + "wms",
    "name": layerName,
    "title": layerTitle,
    "visibility": visibility,
    "format": "image/png8",
    "tiled": true
    }, group && {group} || {});
}
function configRefLayer(baseurl, layerName, layerId, layerTitle, style, visibility = true, group) {
    return style ? assign({
    "id": layerId,
    "type": "wms",
    "url": baseurl + "wms",
    "name": layerName,
    "title": layerTitle,
    "visibility": visibility,
    "format": "image/png8",
    "tiled": true,
    "style": style
  }, group && {group} || {}) : configLayer(baseurl, layerName, layerId, layerTitle, visibility, group);
}
function getViewParamCosts(dim, riskAnalysis) {
    const {dimensions} = riskAnalysis.riskAnalysisData.data;
    const dim1Val = dimensions[dim.dim1] && dimensions[dim.dim1].values[dim.dim1Idx];
    const dim1SearchDim = dimensions[dim.dim1] && dimensions[dim.dim1].layers[dim1Val] && dimensions[dim.dim1].layers[dim1Val].layerReferenceAttribute;
    return {env: `${dim1SearchDim}_opacity:1.0`};
}
function getViewParamRisks(dim, showSubUnit, riskAnalysis) {
    const {dimensions} = riskAnalysis.riskAnalysisData.data;
    const {wms} = riskAnalysis;
    const dim1Val = dimensions[dim.dim1] && dimensions[dim.dim1].values[dim.dim1Idx];
    const dim2Val = dimensions[dim.dim2] && dimensions[dim.dim2].values[dim.dim2Idx];
    const dim1SearchDim = dimensions[dim.dim1] && dimensions[dim.dim1].layers[dim1Val] && dimensions[dim.dim1].layers[dim1Val].layerAttribute;
    const dim2SearchDim = dimensions[dim.dim2] && dimensions[dim.dim2].layers[dim2Val] && dimensions[dim.dim2].layers[dim2Val].layerAttribute;
    let viewparams = wms.viewparams.replace(`${dim1SearchDim}:{}`, `${dim1SearchDim}:${dim1Val}`).replace(`${dim2SearchDim}:{}`, `${dim2SearchDim}:${dim2Val}`);
    if (showSubUnit) {
        const admCode = viewparams.match(/(adm_code:)\w+/g)[0];
        const supCode = admCode.replace(/(adm_code:)/, "sub_adm_code:");
        const superCode = admCode.replace(/(adm_code:)/, "super_adm_code:");
        viewparams = viewparams.replace(admCode, `${supCode};${superCode}`);
    }
    return {viewparams};
}
function getViewParam({dim, showSubUnit, riskAnalysis, app} = {}) {
    return app === 'costs' ? getViewParamCosts(dim, riskAnalysis) : getViewParamRisks(dim, showSubUnit, riskAnalysis);
}
function getLayerTitleRisks(riskAnalysis) {
    const {layer} = riskAnalysis.riskAnalysisData;
    return layer && layer.layerTitle;
}
function getLayerTitleCosts(riskAnalysis) {
    const {referenceLayer} = riskAnalysis.riskAnalysisData;
    return referenceLayer && referenceLayer.layerTitle;
}
function getLayerTitle({riskAnalysis, app}) {
    return app === 'costs' ? getLayerTitleCosts(riskAnalysis) : getLayerTitleRisks(riskAnalysis);
}

function getLayerNameRisks(riskAnalysis) {
    const {layer} = riskAnalysis.riskAnalysisData;
    return layer && layer.layerName;
}
function getLayerNameCosts(riskAnalysis) {
    const {referenceLayer} = riskAnalysis.riskAnalysisData;
    return referenceLayer && referenceLayer.layerName;
}
function getLayerName({riskAnalysis, app}) {
    return app === 'costs' ? getLayerNameCosts(riskAnalysis) : getLayerNameRisks(riskAnalysis);
}
function getStyleRisks(riskAnalysis) {
    const {layer} = riskAnalysis.riskAnalysisData;
    return layer.layerStyle && layer.layerStyle.name;
}
function getStyleCosts(riskAnalysis) {
    const {referenceStyle} = riskAnalysis.riskAnalysisData;
    return referenceStyle.name && referenceStyle.name;
}
function getStyleRef(riskAnalysis) {
    return riskAnalysis && riskAnalysis.riskAnalysisData && riskAnalysis.riskAnalysisData.referenceStyle && riskAnalysis.riskAnalysisData.referenceStyle.name || null;
}
function getStyle({riskAnalysis, app}) {
    return app === 'costs' ? getStyleCosts(riskAnalysis) : getStyleRisks(riskAnalysis);
}

function makeNotificationRow(data) {
    const attributes = Object.keys(data);
    attributes.sort();
    // ['abstract', 'category', 'date', 'details', 'license', 'text', 'thumbnail', 'title', 'uuid'];
    const match = ['abstract', 'category', 'details'];
    const links = ['details'];
    return attributes.filter((val) => {
        return match.indexOf(val) !== -1;
    }).map((item, idx) => {
        let obj = data[item];
        return isString(obj) ? (
            <div key={idx}>
            { links.indexOf(item) === -1 ? (
              <div>
                <div className="disaster-more-info-even">{item}</div>
                <div className="disaster-more-info-odd">{obj}</div>
              </div>
            ) : <a className="text-center" target="_blank" href={obj}>{item}</a>}
            </div>
        ) : null;
    });
}

function makeNotificationBlock(data) {
    return data.map((obj, idx) => {
        return (<div key={idx}><h4 className="disaster-more-info-table-title text-center">{obj.title}</h4>
            <div className="disaster-more-info-table">
                {makeNotificationRow(obj)}
            </div>
        </div>);
    });
}

function makeNotificationBody(data, title, head) {
    return (
        <div className="disaster-more-info-table-notification">
            {title}
            <div className="disaster-more-info-table-container">
                {head}
                {makeNotificationBlock(data)}
            </div>
        </div>
    );
}

module.exports = {configLayer, getViewParam, getLayerName, getStyle, getStyleRef, configRefLayer, getLayerTitle, makeNotificationBody};
