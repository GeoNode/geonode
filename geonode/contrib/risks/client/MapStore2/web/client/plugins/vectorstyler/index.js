/**
* Copyright 2016, GeoSolutions Sas.
* All rights reserved.
*
* This source code is licensed under the BSD-style license found in the
* LICENSE file in the root directory of this source tree.
*/
const {connect} = require('react-redux');
const {setVectorStyleParameter} = require('../../actions/vectorstyler');

const {symbolselector} = require('../../selectors/vectorstyler');

const StylePolygon = connect(symbolselector, {
    setStyleParameter: setVectorStyleParameter.bind(null, 'symbol')
})(require('../../components/style/StylePolygon'));

const StylePoint = connect(symbolselector, {
    setStyleParameter: setVectorStyleParameter.bind(null, 'symbol')
})(require('../../components/style/StylePoint'));

const StylePolyline = connect(symbolselector, {
    setStyleParameter: setVectorStyleParameter.bind(null, 'symbol')
})(require('../../components/style/StylePolyline'));

const ScaleDenominator = require("../../components/style/ScaleDenominator");

module.exports = {
    StylePolygon,
    StylePolyline,
    StylePoint,
    ScaleDenominator
};
