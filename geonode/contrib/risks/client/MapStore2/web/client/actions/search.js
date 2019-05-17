/*
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const TEXT_SEARCH_STARTED = 'TEXT_SEARCH_STARTED';
const TEXT_SEARCH_RESULTS_LOADED = 'TEXT_SEARCH_RESULTS_LOADED';
const TEXT_SEARCH_PERFORMED = 'TEXT_SEARCH_PERFORMED';
const TEXT_SEARCH_RESULTS_PURGE = 'TEXT_SEARCH_RESULTS_PURGE';
const TEXT_SEARCH_RESET = 'TEXT_SEARCH_RESET';
const TEXT_SEARCH_ADD_MARKER = 'TEXT_SEARCH_ADD_MARKER';
const TEXT_SEARCH_TEXT_CHANGE = 'TEXT_SEARCH_TEXT_CHANGE';
const TEXT_SEARCH_LOADING = 'TEXT_SEARCH_LOADING';
const TEXT_SEARCH_NESTED_SERVICES_SELECTED = 'TEXT_SEARCH_NESTED_SERVICE_SELECTED';
const TEXT_SEARCH_ERROR = 'TEXT_SEARCH_ERROR';
const TEXT_SEARCH_CANCEL_ITEM = 'TEXT_SEARCH_CANCEL_ITEM';
const TEXT_SEARCH_ITEM_SELECTED = 'TEXT_SEARCH_ITEM_SELECTED';
/**
 * updates the results of the search result loaded
 * @memberof actions.search
 * @param {geojsonFeature[]} results array of search results
 * @param {boolean} append [false] tells to append the result to existing ones or not
 * @param {object[]} servies services intrested to use for the next search
 */
function searchResultLoaded(results, append=false, services) {
    return {
        type: TEXT_SEARCH_RESULTS_LOADED,
        results: results,
        append: append,
        services
    };
}
/**
 * updates the search text
 * @memberof actions.search
 * @param {string} text the new text
 */
function searchTextChanged(text) {
    return {
        type: TEXT_SEARCH_TEXT_CHANGE,
        searchText: text
    };
}
/**
 * trigger search text loading
 * @memberof actions.search
 * @param {boolean} loading boolean flag
 */
function searchTextLoading(loading) {
    return {
        type: TEXT_SEARCH_LOADING,
        loading
    };
}

/**
 * an error occurred during text searchText
 * @memberof actions.search
 * @param error the error
 */
function searchResultError(error) {
    return {
        type: TEXT_SEARCH_ERROR,
        error
    };
}

/**
 * clear the results
 * @memberof actions.search
 */
function resultsPurge() {
    return {
        type: TEXT_SEARCH_RESULTS_PURGE
    };
}

/**
 * reset the search text and clear results
 * @memberof actions.search
 */
function resetSearch() {
    return {
        type: TEXT_SEARCH_RESET
    };
}

/**
 * add a marker to the search result layer
 * @memberof actions.search
 * @param {object} itemPosition
 */
function addMarker(itemPosition) {
    return {
        type: TEXT_SEARCH_ADD_MARKER,
        markerPosition: itemPosition
    };
}

/**
 * perform a text search
 * @memberof actions.search
 * @param {string} searchText the text to search
 * @param {object} options [{}] the search options. Contain the services
 */
function textSearch(searchText, {services = null} = {}) {
    return {
        type: TEXT_SEARCH_STARTED,
        searchText,
        services
    };
}

/**
 * Trigger when an item is selected from the search results
 * @memberof actions.search
 * @param {object} item the selected item
 * @param {object} mapConfig the current map configuration (with size, projection...)
 */
function selectSearchItem(item, mapConfig) {
    return {
        type: TEXT_SEARCH_ITEM_SELECTED,
        item,
        mapConfig
    };

}

/**
 * Configures the search tool to perform sub-service queries. It will store the
 * selected item and configure the new nested services.
 * @memberof actions.search
 * @param {object[]} services the of the nested services
 * @param {object[]} items the selected items
 * @param {object[]} searchText the new search text
 */
function selectNestedService(services, items, searchText) {
    return {
        type: TEXT_SEARCH_NESTED_SERVICES_SELECTED,
        searchText,
        services,
        items
    };
}

/**
 * remove an item selected ()
 * @memberof actions.search
 * @param {object} item the item to remove
 */
function cancelSelectedItem(item) {
    return {
        type: TEXT_SEARCH_CANCEL_ITEM,
        item
    };
}

/**
 * Actions for search
 * @name actions.search
 */
module.exports = {
    TEXT_SEARCH_STARTED,
    TEXT_SEARCH_LOADING,
    TEXT_SEARCH_ERROR,
    TEXT_SEARCH_RESULTS_LOADED,
    TEXT_SEARCH_PERFORMED,
    TEXT_SEARCH_RESULTS_PURGE,
    TEXT_SEARCH_RESET,
    TEXT_SEARCH_ADD_MARKER,
    TEXT_SEARCH_TEXT_CHANGE,
    TEXT_SEARCH_ITEM_SELECTED,
    TEXT_SEARCH_NESTED_SERVICES_SELECTED,
    TEXT_SEARCH_CANCEL_ITEM,
    searchTextLoading,
    searchResultError,
    searchResultLoaded,
    textSearch,
    resultsPurge,
    resetSearch,
    addMarker,
    searchTextChanged,
    selectNestedService,
    selectSearchItem,
    cancelSelectedItem
};
