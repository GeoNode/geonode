/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const {connect} = require('react-redux');


const {loadMaps, mapsSearchTextChanged} = require('../actions/maps');
const ConfigUtils = require('../utils/ConfigUtils');

const SearchBar = connect((state) => ({
    className: "maps-search",
    hideOnBlur: false,
    placeholderMsgId: "maps.search",
    typeAhead: false,
    start: state && state.maps && state.maps.start,
    limit: state && state.maps && state.maps.limit,
    searchText: (state.maps && state.maps.searchText !== '*' && state.maps.searchText) || ""
}), {
    onSearchTextChange: mapsSearchTextChanged,
    onSearch: (text, options) => {
        let searchText = (text && text !== "") ? (text) : ConfigUtils.getDefaults().initialMapFilter || "*";
        return loadMaps(ConfigUtils.getDefaults().geoStoreUrl, searchText, options);
    },
    onSearchReset: loadMaps.bind(null, ConfigUtils.getDefaults().geoStoreUrl, ConfigUtils.getDefaults().initialMapFilter || "*")
}, (stateProps, dispatchProps) => {

    return {
        ...stateProps,
        onSearch: (text) => {
            let limit = stateProps.limit;
            dispatchProps.onSearch(text, {start: 0, limit});
        },
        onSearchReset: () => {
            dispatchProps.onSearchReset({start: 0, limit: stateProps.limit});
        },
        onSearchTextChange: dispatchProps.onSearchTextChange
    };
})(require("../components/mapcontrols/search/SearchBar"));

module.exports = {
    MapSearchPlugin: SearchBar,
    reducers: {maps: require('../reducers/maps')}
};
