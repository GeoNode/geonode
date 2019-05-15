/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const expect = require('expect');
const {jsonToSLD, vecStyleToSLD} = require('../SLDUtils');

const rasterstylerstate = {
    redband: {band: '1', contrast: 'GammaValue', algorithm: "none", gammaValue: 1, min: 1, max: 255},
    blueband: {band: '3', contrast: 'none', algorithm: "none", gammaValue: 1, min: 1, max: 255},
    greenband: {band: '2', contrast: 'none', algorithm: "none", gammaValue: 1, min: 1, max: 255},
    grayband: {band: '1', contrast: 'none', algorithm: "none", gammaValue: 1, min: 1, max: 255},
    pseudocolor: {colorMapEntry: [{color: "#eff3ff", quantity: 0, label: "0.00"}], type: "ramp", opacity: "1.00"},
    pseudoband: {band: "1", contrast: "Normalize", algorithm: "ClipToMinimumMaximum", min: 1, max: 255}
};
const layer = {name: "sde:HYP_HR_SR_OB_DR"};


describe('SLDUtils', () => {

    it('convert rasterlayer state to sld strings', () => {
        let pseudo = jsonToSLD({
            styletype: "pseudo",
            opacity: "0.50",
            state: rasterstylerstate,
            layer: layer});
        expect(pseudo).toExist();
        let rgb = jsonToSLD(
            {
            styletype: "rgb",
            opacity: "0.50",
            state: rasterstylerstate,
            layer: layer
        });
        expect(rgb).toExist();
        let gray = jsonToSLD({
            styletype: "gray",
            opacity: "0.50",
            state: rasterstylerstate,
            layer: layer
        });
        expect(gray).toExist();
    });
    it('test vectorlayer state to sld strings', () => {
        let rules = [
        {
            "id": "bd8587a0-543a-11e6-a812-3f41916af8df",
            "symbol": {
                "type": "Point",
                "color": {"r": 0, "g": 0, "b": 255, "a": 1},
                "width": 3,
                "fill": {"r": 0, "g": 0, "b": 255, "a": 0.1},
                "radius": 10,
                "marker": false,
                "markName": "circle"
            },
            "name": "Test Name"},
        {
            "id": "dfcce690-543b-11e6-a812-3f41916af8df",
            "symbol": {
                "type": "Polygon",
                "color": {"r": 0, "g": 0, "b": 255, "a": 1},
                "width": 3,
                "fill": {"r": 0, "g": 0, "b": 255, "a": 0.1}
            },
            "name": "Test Name"},
        {
            "id": "406d88b0-543c-11e6-a812-3f41916af8df",
            "symbol": {
                "type": "Line",
                "color": {"r": 0, "g": 0, "b": 255, "a": 1},
                "width": 3
            },
            "name": "Test Name",
            "minDenominator": 73957338.86364141,
            "maxDenominator": 295829355.45456564}
        ];
        let result = `<sld:StyledLayerDescriptor xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0"><sld:NamedLayer><sld:Name>sde:HYP_HR_SR_OB_DR</sld:Name><sld:UserStyle><sld:FeatureTypeStyle><sld:Rule><PointSymbolizer xsi:type="sld:PointSymbolizer" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><sld:Graphic><sld:Mark><sld:WellKnownName>circle</sld:WellKnownName><sld:Fill><sld:CssParameter name="fill">#0000ff</sld:CssParameter><sld:CssParameter name="fill-opacity">0.1</sld:CssParameter></sld:Fill><sld:Stroke><sld:CssParameter name="stroke">#0000ff</sld:CssParameter><sld:CssParameter name="stroke-opacity">1</sld:CssParameter><sld:CssParameter name="stroke-width">3</sld:CssParameter></sld:Stroke></sld:Mark><sld:Size>10</sld:Size></sld:Graphic></PointSymbolizer></sld:Rule><sld:Rule><PolygonSymbolizer xsi:type="sld:PolygonSymbolizer" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><sld:Fill><sld:CssParameter name="fill">#0000ff</sld:CssParameter><sld:CssParameter name="fill-opacity">0.1</sld:CssParameter></sld:Fill><sld:Stroke><sld:CssParameter name="stroke">#0000ff</sld:CssParameter><sld:CssParameter name="stroke-opacity">1</sld:CssParameter><sld:CssParameter name="stroke-width">3</sld:CssParameter></sld:Stroke></PolygonSymbolizer></sld:Rule><sld:Rule><sld:MinScaleDenominator>73957338.86364141</sld:MinScaleDenominator><sld:MaxScaleDenominator>295829355.45456564</sld:MaxScaleDenominator><LineSymbolizer xsi:type="sld:LineSymbolizer" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><sld:Stroke><sld:CssParameter name="stroke">#0000ff</sld:CssParameter><sld:CssParameter name="stroke-opacity">1</sld:CssParameter><sld:CssParameter name="stroke-width">3</sld:CssParameter></sld:Stroke></LineSymbolizer></sld:Rule></sld:FeatureTypeStyle></sld:UserStyle></sld:NamedLayer></sld:StyledLayerDescriptor>`;
        let sld = vecStyleToSLD({
            rules,
            layer});
        expect(sld).toExist();
        expect(sld).toEqual(result);
    });
});
