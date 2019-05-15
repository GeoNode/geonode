/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const {connect} = require('react-redux');
const {selectFeatures, dockSizeFeatures} = require('../actions/featuregrid');
const {query, closeResponse} = require('../actions/wfsquery');
const {changeMapView} = require('../actions/map');

module.exports = {
    FeatureGridPlugin: connect((state) => ({
        open: state.query && state.query.open,
        features: state.query && state.query.result && state.query.result.features,
        filterObj: state.query && state.query.filterObj,
        searchUrl: state.query && state.query.searchUrl,
        initWidth: "100%",
        map: (state.map && state.map.present) || (state.map) || (state.config && state.config.map) || null,
        columnsDef: state.query && state.query.typeName && state.query.featureTypes
            && state.query.featureTypes[state.query.typeName]
            && state.query.featureTypes[state.query.typeName]
            && state.query.featureTypes[state.query.typeName].attributes
            && state.query.featureTypes[state.query.typeName].attributes.filter(attr => attr.name !== "geometry")
            .map((attr) => ({
                headerName: attr.label,
                field: attr.attribute
            })),
        query: state.query && state.query.queryObj,
        isNew: state.query && state.query.isNew,
        totalFeatures: state.query && state.query.result && state.query.result.totalFeatures,
        dockSize: state.highlight && state.highlight.dockSize
    }),
    {
        selectFeatures,
        changeMapView,
        onQuery: query,
        onBackToSearch: closeResponse,
        setDockSize: dockSizeFeatures
    })(require('../components/data/featuregrid/DockedFeatureGrid')),
    reducers: {highlight: require('../reducers/featuregrid')}
};
