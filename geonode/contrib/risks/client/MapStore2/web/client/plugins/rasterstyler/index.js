/**
* Copyright 2016, GeoSolutions Sas.
* All rights reserved.
*
* This source code is licensed under the BSD-style license found in the
* LICENSE file in the root directory of this source tree.
*/

const {connect} = require('react-redux');
const {setRasterStyleParameter} = require('../../actions/rasterstyler');

const RedBandSelector = connect((state) => { return state.rasterstyler.redband || {}; },
    {
        onChange: setRasterStyleParameter.bind(null, 'redband')
    })(require('../../components/style/BandSelector'));

const BlueBandSelector = connect((state) => { return state.rasterstyler.blueband || {}; },
    {
        onChange: setRasterStyleParameter.bind(null, 'blueband')
    })(require('../../components/style/BandSelector'));

const GreenBandSelector = connect((state) => { return state.rasterstyler.greenband || {}; },
    {
        onChange: setRasterStyleParameter.bind(null, 'greenband')
    })(require('../../components/style/BandSelector'));

const GrayBandSelector = connect((state) => { return state.rasterstyler.grayband || {}; },
    {
        onChange: setRasterStyleParameter.bind(null, 'grayband')
    })(require('../../components/style/BandSelector'));
const PseudoBandSelector = connect((state) => { return state.rasterstyler.pseudoband || {}; },
{
    onChange: setRasterStyleParameter.bind(null, 'pseudoband')
})(require('../../components/style/BandSelector'));

const RasterStyleTypePicker = connect((state) => { return state.rasterstyler.typepicker || {}; },
    {
        onChange: setRasterStyleParameter.bind(null, 'typepicker')
    })(require('../../components/style/RasterStyleTypePicker'));

const OpacityPicker = connect((state) => { return state.rasterstyler.opacitypicker || {}; },
    {
        onChange: setRasterStyleParameter.bind(null, 'opacitypicker')
    })(require('../../components/style/OpacityPicker'));

const EqualInterval = connect((state) => { return state.rasterstyler.equalinterval || {}; },
    {
        onChange: setRasterStyleParameter.bind(null, 'equalinterval')
    })(require('../../components/style/EqualInterval'));

const PseudoColor = connect((state) => { return state.rasterstyler.pseudocolor || {}; },
    {
        onChange: setRasterStyleParameter.bind(null, 'pseudocolor')
    })(require('../../components/style/PseudoColorSettings'));

module.exports = {
    RedBandSelector,
    BlueBandSelector,
    GreenBandSelector,
    GrayBandSelector,
    PseudoBandSelector,
    RasterStyleTypePicker,
    EqualInterval,
    PseudoColor,
    OpacityPicker
};
