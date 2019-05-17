/**
* Copyright 2016, GeoSolutions Sas.
* All rights reserved.
*
* This source code is licensed under the BSD-style license found in the
* LICENSE file in the root directory of this source tree.
*/
const {connect} = require('react-redux');

const {onShapeError} = require('../../actions/shapefile');
const {setStyleParameter} = require('../../actions/style');

const ShapeFileUploadAndStyle = connect((state) => (
        {
            uploadOptions: {
            error: state.shapefile && state.shapefile.error || null,
            loading: state.shapefile && state.shapefile.loading || false }
            }
        ), {
    onShapeError: onShapeError
})(require('../../components/shapefile/ShapefileUploadAndStyle'));

const StylePolygon = connect((state) => (
        {
            shapeStyle: state.style || {}
        }
        ), {
    setStyleParameter: setStyleParameter
})(require('../../components/style/StylePolygon'));

const StylePoint = connect((state) => (
        {
            shapeStyle: state.style || {}
        }
        ), {
    setStyleParameter: setStyleParameter
})(require('../../components/style/StylePoint'));

const StylePolyline = connect((state) => (
        {
            shapeStyle: state.style || {}
        }
        ), {
    setStyleParameter: setStyleParameter
})(require('../../components/style/StylePolyline'));

module.exports = {
    ShapeFileUploadAndStyle,
    StylePolygon,
    StylePolyline,
    StylePoint
};
