/*
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');
const {connect} = require('react-redux');
const {createSelector} = require('reselect');

const assign = require('object-assign');

const HelpWrapper = require('./help/HelpWrapper');
const Message = require('./locale/Message');

const {get} = require('lodash');

const {resultsPurge, resetSearch, addMarker, searchTextChanged, textSearch, selectSearchItem, cancelSelectedItem} = require("../actions/search");

const searchSelector = createSelector([
    state => state.search || null
], (searchState) => ({
    error: searchState && searchState.error,
    loading: searchState && searchState.loading,
    searchText: searchState ? searchState.searchText : "",
    selectedItems: searchState && searchState.selectedItems,
    selectedServices: searchState && searchState.selectedServices
}));

const SearchBar = connect(searchSelector, {
    // ONLY FOR SAMPLE - The final one will get from state and simply call textSearch
    onSearch: textSearch,
    onPurgeResults: resultsPurge,
    onSearchReset: resetSearch,
    onSearchTextChange: searchTextChanged,
    onCancelSelectedItem: cancelSelectedItem
})(require("../components/mapcontrols/search/SearchBar"));

const {mapSelector} = require('../selectors/map');
const {isArray} = require('lodash');

const MediaQuery = require('react-responsive');

const selector = createSelector([
    mapSelector,
    state => state.search || null
], (mapConfig, searchState) => ({
    mapConfig,
    results: searchState ? searchState.results : null
}));

const SearchResultList = connect(selector, {
    onItemClick: selectSearchItem,
    addMarker: addMarker
})(require('../components/mapcontrols/search/SearchResultList'));

const ToggleButton = require('./searchbar/ToggleButton');

/**
 * Search plugin. Provides search functionalities for the map.
 * Allows to display results and place them on the map. Supports nominatim and WFS as search protocols
 * You can configure the services and each service can trigger a nested search.
 *
 * @example
 * {
 *  "name": "Search",
 *  "cfg": {
 *    "withToggle": ["max-width: 768px", "min-width: 768px"]
 *  }
 * }
 * @class Search
 * @memberof plugins
 * @prop {object} cfg.searchOptions initial search options
 * @prop {searchService[]} cfg.searchOptions.services a list of services to perform search.
 * a **nominatim** search service look like this:
 * ```
 * {
 *  "type": "nominatim",
 *  "searchTextTemplate": "${properties.display_name}", // text to use as searchText when an item is selected. Gets the result properties.
 *  "options": {
 *    "polygon_geojson": 1,
 *    "limit": 3
 *  }
 * ```
 *
 * a **wfs** service look like this:
 * ```
 * {
 *      "type": "wfs",
 *      "priority": 2,
 *      "displayName": "${properties.propToDisplay}",
 *      "subTitle": " (a subtitle for the results coming from this service [ can contain expressions like ${properties.propForSubtitle}])",
 *      "options": {
 *        "url": "/geoserver/wfs",
 *        "typeName": "workspace:layer",
 *        "queriableAttributes": ["attribute_to_query"],
 *        "sortBy": "ID",
 *        "srsName": "EPSG:4326",
 *        "maxFeatures": 4
 *      },
 *      "nestedPlaceholder": "Write other text to refine the search...",
 *      "then": [ ... an array of services to use when one item of this service is selected]
 *  }
 * ```
 * The typical nested service needs to have some additional parameters:
 * ```
 * {
 *     "type": "wfs",
 *     "filterTemplate": " AND SOMEPROP = '${properties.OLDPROP}'", // will be appended to the original filter, it gets the properties of the current selected item (of the parent service)
 *     "options": {
 *       ...
 *     }
 * }
 * ```
 * **note:** `searchTextTemplate` is useful to populate the search text input when a search result is selected, typically with "leaf" services.
 * @prop {array|boolean} cfg.withToggle when boolean, true uses a toggle to display the searchbar. When array, e.g  `["max-width: 768px", "min-width: 768px"]`, `max-width` and `min-width` are the limits where to show/hide the toggle (useful for mobile)
 */
const SearchPlugin = connect((state) => ({
    enabled: state.controls && state.controls.search && state.controls.search.enabled || false,
    selectedServices: state && state.search && state.search.selectedServices,
    selectedItems: state && state.search && state.search.selectedItems
}))(React.createClass({
    propTypes: {
        searchOptions: React.PropTypes.object,
        selectedItems: React.PropTypes.array,
        selectedServices: React.PropTypes.array,
        withToggle: React.PropTypes.oneOfType([React.PropTypes.bool, React.PropTypes.array]),
        enabled: React.PropTypes.bool
    },
    getDefaultProps() {
        return {
            searchOptions: {
                services: [{type: "nominatim"}]
            },
            withToggle: false,
            enabled: true
        };
    },
    getServiceOverrides( propSelector ) {
        return this.props.selectedItems && this.props.selectedItems[this.props.selectedItems.length - 1] && get(this.props.selectedItems[this.props.selectedItems.length - 1], propSelector);
    },
    getCurrentServices() {
        return this.props.selectedServices && this.props.selectedServices.length > 0 ? assign({}, this.props.searchOptions, {services: this.props.selectedServices}) : this.props.searchOptions;
    },
    getSearchAndToggleButton() {
        const search = (<SearchBar
            key="seachBar"
            {...this.props}
            searchOptions={this.getCurrentServices()}
            placeholder={this.getServiceOverrides("placeholder")}
            />);
        if (this.props.withToggle === true) {
            return [<ToggleButton/>].concat(this.props.enabled ? [search] : null);
        }
        if (isArray(this.props.withToggle)) {
            return (
                    <span><MediaQuery query={"(" + this.props.withToggle[0] + ")"}>
                        <ToggleButton/>
                        {this.props.enabled ? search : null}
                    </MediaQuery>
                    <MediaQuery query={"(" + this.props.withToggle[1] + ")"}>
                        {search}
                    </MediaQuery>
                </span>
            );
        }
        return search;
    },
    render() {
        return (<span>
            <HelpWrapper
                id="search-help"
                key="seachBar-help"
                    helpText={<Message msgId="helptexts.searchBar"/>}>
                    {this.getSearchAndToggleButton()}
                </HelpWrapper>
                <SearchResultList searchOptions={this.props.searchOptions} key="nominatimresults"/>
            </span>
        );
    }
}));
const {searchEpic, searchItemSelected} = require('../epics/search');

module.exports = {
    SearchPlugin: assign(SearchPlugin, {
        OmniBar: {
            name: 'search',
            position: 1,
            tool: true,
            priority: 1
        }
    }),
    epics: {searchEpic, searchItemSelected},
    reducers: {
        search: require('../reducers/search'),
        mapInfo: require('../reducers/mapInfo')
    }
};
