/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {connect} = require('react-redux');

const Message = require('./locale/Message');

const {onShapeError, shapeLoading, onShapeChoosen, onSelectLayer, onLayerAdded, updateShapeBBox, onShapeSuccess} = require('../actions/shapefile');
const {zoomToExtent} = require('../actions/map');
const {addLayer} = require('../actions/layers');
const {toggleControl} = require('../actions/controls');

const assign = require('object-assign');
const {Glyphicon} = require('react-bootstrap');

module.exports = {
    ShapeFilePlugin: assign({loadPlugin: (resolve) => {
        require.ensure(['./shapefile/ShapeFile'], () => {
            const ShapeFile = require('./shapefile/ShapeFile');

            const ShapeFilePlugin = connect((state) => (
            {
                visible: state.controls && state.controls.shapefile && state.controls.shapefile.enabled,
                layers: state.shapefile && state.shapefile.layers || null,
                selected: state.shapefile && state.shapefile.selected || null,
                bbox: state.shapefile && state.shapefile.bbox || null,
                success: state.shapefile && state.shapefile.success || null,
                error: state.shapefile && state.shapefile.error || null,
                shapeStyle: state.style || {}
            }
            ), {
                onShapeChoosen: onShapeChoosen,
                onLayerAdded: onLayerAdded,
                onSelectLayer: onSelectLayer,
                onShapeError: onShapeError,
                onShapeSuccess: onShapeSuccess,
                addShapeLayer: addLayer,
                onZoomSelected: zoomToExtent,
                updateShapeBBox: updateShapeBBox,
                shapeLoading: shapeLoading,
                toggleControl: toggleControl.bind(null, 'shapefile', null)
            })(ShapeFile);

            resolve(ShapeFilePlugin);
        });
    }, enabler: (state) => state.shapefile && state.shapefile.enabled || state.toolbar && state.toolbar.active === 'shapefile'}, {
        Toolbar: {
            name: 'shapefile',
            position: 9,
            panel: true,
            help: <Message msgId="helptexts.shapefile"/>,
            title: "shapefile.title",
            tooltip: "shapefile.tooltip",
            wrap: true,
            icon: <Glyphicon glyph="open-file"/>,
            exclusive: true,
            priority: 1
        },
        BurgerMenu: {
            name: 'shapefile',
            position: 4,
            text: <Message msgId="shapefile.title"/>,
            icon: <Glyphicon glyph="upload"/>,
            action: toggleControl.bind(null, 'shapefile', null),
            priority: 2,
            doNotHide: true
        }
    }),
    reducers: {
        shapefile: require('../reducers/shapefile'),
        style: require('../reducers/style')
    }
};
