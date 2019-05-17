/*
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var {TEXT_SEARCH_RESULTS_LOADED, TEXT_SEARCH_RESULTS_PURGE, TEXT_SEARCH_RESET, TEXT_SEARCH_ADD_MARKER, TEXT_SEARCH_TEXT_CHANGE, TEXT_SEARCH_LOADING, TEXT_SEARCH_ERROR,
    TEXT_SEARCH_NESTED_SERVICES_SELECTED, TEXT_SEARCH_CANCEL_ITEM} = require('../actions/search');
var {RESET_CONTROLS} = require('../actions/controls');

const assign = require('object-assign');
/**
 * Manages the state of the map search with it's results
 * The properties represent the shape of the state
 * @prop {boolan} loading loading state
 * @prop {object} error the last error, if any
 * @prop {string} searchText the search text
 * @prop {array}  results the results
 * @prop {object} markerPosition  the markerPosition
 * @prop {object} selectedServicess tores the services currently selected by the user
 * @prop {object} selectedItems the selected items
 *
 * @example
 *{
 *  search: {
 *    searchText: 'test',
 *    error: null,
 *    loading: false,
 *    results: [
 *      {
 *        properties: {
 *          place_id: '130504451',
 *          licence: 'Data © OpenStreetMap contributors, ODbL 1.0. http://www.openstreetmap.org/copyright',
 *          osm_type: 'way',
 *          osm_id: '294145572',
 *          lat: '6.82439805',
 *          lon: '81.0004103985287',
 *          display_name: 'test, Bandarawela, Badulla District, Uva, Sri Lanka',
 *          'class': 'landuse',
 *          type: 'forest',
 *          importance: 0.31,
 *        },
 *        id: '294145572',
 *        type: 'Feature',
 *        bbox: [
 *          81.0001165,
 *          6.8238999,
 *          81.0008042,
 *          6.8248084
 *        ],
 *        geometry: {
 *          type: 'Polygon',
 *          coordinates: [
 *              [[ 81.0001165, 6.8242576],
 *              [81.0001892, 6.8245385],
 *              [81.0003879, 6.8248084],
 *              [81.0008042, 6.8241984],
 *              [81.0003606, 6.8238999],
 *              [81.0001165, 6.8242576]
 *            ]]
 *        },
 *        __SERVICE__: {
 *          type: 'nominatim'
 *        },
 *        __PRIORITY__: 0
 *      },
 *    ]
 *  }
 *}
 * @memberof reducers
 */
function search(state = null, action) {
    switch (action.type) {
        case TEXT_SEARCH_LOADING: {
            return assign({}, state, {loading: action.loading});
        }
        case TEXT_SEARCH_ERROR: {
            return assign({}, state, {error: action.error});
        }
        case TEXT_SEARCH_TEXT_CHANGE:
            return assign({}, state, { searchText: action.searchText, error: null });
        case TEXT_SEARCH_RESULTS_LOADED:
            let results = action.results;
            if (action.append === true && state && state.results) {
                results = [...state.results, ...action.results];
            }
            return assign({}, state, { results: results, error: null });
        case TEXT_SEARCH_RESULTS_PURGE:
            return assign({}, state, { results: null, error: null});
        case TEXT_SEARCH_ADD_MARKER:
            return assign({}, state, { markerPosition: action.markerPosition });
        case TEXT_SEARCH_RESET:
        case RESET_CONTROLS:
            return null;
        case TEXT_SEARCH_NESTED_SERVICES_SELECTED:
            return assign({}, state, {
                selectedServices: action.services,
                searchText: action.searchText,
                selectedItems: (state.selectedItems || []).concat(action.items)
             });
        case TEXT_SEARCH_CANCEL_ITEM:
            return assign({}, {
                selectedItems: state.selectedItems && state.selectedItems.filter(item => item !== action.item),
                searchText: state.searchText === "" && action.item && action.item.text ? action.item.text.substring(0, action.item.text.length) : state.searchText
            });
        default:
            return state;
    }
}

module.exports = search;
