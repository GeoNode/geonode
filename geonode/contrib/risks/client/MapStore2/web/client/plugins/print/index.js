/**
* Copyright 2016, GeoSolutions Sas.
* All rights reserved.
*
* This source code is licensed under the BSD-style license found in the
* LICENSE file in the root directory of this source tree.
*/
const React = require('react');
const {connect} = require('react-redux');
const {compose} = require('redux');
const ConfigUtils = require('../../utils/ConfigUtils');
const {FormControl, FormGroup, ControlLabel} = require('react-bootstrap');

const {setPrintParameter, changePrintZoomLevel, changeMapPrintPreview, printCancel} =
    require('../../actions/print');

const {setControlProperty} = require('../../actions/controls');

const TextWithLabel = (props) => {
    return (
      <FormGroup>
        {props.label && <ControlLabel>{props.label}</ControlLabel> || null}
        <FormControl {...props}/>
      </FormGroup>
    );
};

const Name = connect((state) => ({
    value: state.print && state.print.spec && state.print.spec.name || '',
    type: "text"
}), {
    onChange: compose(setPrintParameter.bind(null, 'name'), (e) => e.target.value)
})(TextWithLabel);

const Description = connect((state) => ({
    value: state.print && state.print.spec && state.print.spec.description || '',
    componentClass: "textarea"
}), {
    onChange: compose(setPrintParameter.bind(null, 'description'), (e) => e.target.value)
})(TextWithLabel);

const Resolution = connect((state) => ({
    selected: state.print && state.print.spec && state.print.spec.resolution || '',
    items: state.print && state.print.capabilities && state.print.capabilities.dpis.map((dpi) => ({
        name: dpi.name + ' dpi',
        value: dpi.value
    })) || []
}), {
    onChange: setPrintParameter.bind(null, 'resolution')
})(require('../../components/print/Choice'));

const Sheet = connect((state) => ({
    selected: state.print && state.print.spec && state.print.spec.sheet
}), {
    onChange: setPrintParameter.bind(null, 'sheet')
})(require('../../components/print/Sheet'));

const {currentLayouts, twoPageEnabled} = require('../../selectors/print');

const LegendOption = connect((state) => ({
    checked: state.print && state.print.spec && !!state.print.spec.includeLegend,
    layouts: currentLayouts(state)
}), {
    onChange: setPrintParameter.bind(null, 'includeLegend')
})(require('../../components/print/PrintOption'));

const MultiPageOption = connect((state) => ({
    checked: state.print && state.print.spec.includeLegend && state.print.spec && !!state.print.spec.twoPages,
    layouts: currentLayouts(state),
    isEnabled: () => twoPageEnabled(state)
}), {
    onChange: setPrintParameter.bind(null, 'twoPages')
})(require('../../components/print/PrintOption'));

const LandscapeOption = connect((state) => ({
    selected: (state.print && state.print.spec && state.print.spec.landscape) ? 'landscape' : 'portrait',
    layouts: currentLayouts(state),
    options: [{label: 'print.alternatives.landscape', value: 'landscape'}, {label: 'print.alternatives.portrait', value: 'portrait'}]
}), {
    onChange: compose(setPrintParameter.bind(null, 'landscape'), (selected) => selected === 'landscape')
})(require('../../components/print/PrintOptions'));

const ForceLabelsOption = connect((state) => ({
    checked: state.print && state.print.spec && !!state.print.spec.forceLabels
}), {
    onChange: setPrintParameter.bind(null, 'forceLabels')
})(require('../../components/print/PrintOption'));

const AntiAliasingOption = connect((state) => ({
    checked: state.print && state.print.spec && !!state.print.spec.antiAliasing
}), {
    onChange: setPrintParameter.bind(null, 'antiAliasing')
})(require('../../components/print/PrintOption'));

const IconSizeOption = connect((state) => ({
    value: state.print && state.print.spec && state.print.spec.iconSize,
    type: "number"
}), {
    onChange: compose(setPrintParameter.bind(null, 'iconSize'), (e) => parseInt(e.target.value, 10))
})(TextWithLabel);

const LegendDpiOption = connect((state) => ({
    value: state.print && state.print.spec && state.print.spec.legendDpi,
    type: "number"
}), {
    onChange: compose(setPrintParameter.bind(null, 'legendDpi'), (e) => parseInt(e.target.value, 10))
})(TextWithLabel);

const DefaultBackgroundOption = connect((state) => ({
    checked: state.print && state.print.spec && !!state.print.spec.defaultBackground
}), {
    onChange: setPrintParameter.bind(null, 'defaultBackground')
})(require('../../components/print/PrintOption'));

const Font = connect((state) => ({
    family: state.print && state.print.spec && state.print.spec.fontFamily,
    size: state.print && state.print.spec && state.print.spec.fontSize,
    bold: state.print && state.print.spec && state.print.spec.bold,
    italic: state.print && state.print.spec && state.print.spec.italic
}), {
    onChangeFamily: setPrintParameter.bind(null, 'fontFamily'),
    onChangeSize: setPrintParameter.bind(null, 'fontSize'),
    onChangeBold: setPrintParameter.bind(null, 'bold'),
    onChangeItalic: setPrintParameter.bind(null, 'italic')
})(require('../../components/print/Font'));

const MapPreview = connect((state) => ({
    map: state.print && state.print.map,
    layers: state.print && state.print.map && state.print.map.layers || [],
    scales: state.print && state.print.capabilities && state.print.capabilities.scales.slice(0).reverse().map((scale) => parseFloat(scale.value)) || []
}), {
    onChangeZoomLevel: changePrintZoomLevel,
    onMapViewChanges: changeMapPrintPreview
})(require('../../components/print/MapPreview'));

const PrintSubmit = connect((state) => ({
    loading: state.print && state.print.isLoading || false
}))(require('../../components/print/PrintSubmit'));

const PrintPreview = connect((state) => ({
    url: state.print && ConfigUtils.getProxiedUrl(state.print.pdfUrl),
    scale: state.controls && state.controls.print && state.controls.print.viewScale || 0.5,
    currentPage: state.controls && state.controls.print && state.controls.print.currentPage || 0,
    pages: state.controls && state.controls.print && state.controls.print.pages || 1
}), {
    back: printCancel,
    setPage: setControlProperty.bind(null, 'print', 'currentPage'),
    setPages: setControlProperty.bind(null, 'print', 'pages'),
    setScale: setControlProperty.bind(null, 'print', 'viewScale')
})(require('../../components/print/PrintPreview'));

module.exports = {
    Name,
    Description,
    Resolution,
    DefaultBackgroundOption,
    Sheet,
    LegendOption,
    MultiPageOption,
    LandscapeOption,
    ForceLabelsOption,
    AntiAliasingOption,
    IconSizeOption,
    LegendDpiOption,
    Font,
    MapPreview,
    PrintSubmit,
    PrintPreview
};
