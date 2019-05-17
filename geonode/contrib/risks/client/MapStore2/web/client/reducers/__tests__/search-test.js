/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var expect = require('expect');
var search = require('../search');
const {TEXT_SEARCH_RESULTS_LOADED, TEXT_SEARCH_LOADING, TEXT_SEARCH_ERROR, TEXT_SEARCH_RESULTS_PURGE, TEXT_SEARCH_NESTED_SERVICES_SELECTED, TEXT_SEARCH_CANCEL_ITEM} = require('../../actions/search');

describe('Test the search reducer', () => {
    it('search results loading', () => {
        let state = search({}, {
            type: TEXT_SEARCH_LOADING,
            loading: true
        });
        expect(state.loading).toBe(true);
        state = search({}, {
            type: TEXT_SEARCH_LOADING,
            loading: false
        });
        expect(state.loading).toBe(false);
    });
    it('search results error', () => {
        let state = search({}, {
            type: TEXT_SEARCH_ERROR,
            error: {message: "M"}
        });
        expect(state.error).toExist();
    });
    it('search results loaded', () => {
        let testAction1 = {
            type: TEXT_SEARCH_RESULTS_LOADED,
            results: ["result1", "result2"]
        };

        let state = search({error: {}}, testAction1);
        expect(state).toExist();
        expect(state.results).toEqual(["result1", "result2"]);
        expect(state.error).toBe(null);

        let testAction2 = {
            type: TEXT_SEARCH_RESULTS_LOADED,
            results: ["result3", "result4"]
        };

        state = search(state, testAction2);
        expect(state).toExist();
        expect(state.results).toEqual(["result3", "result4"]);

        let testAction3 = {
            type: TEXT_SEARCH_RESULTS_LOADED,
            results: ["result5", "result6"],
            append: true
        };

        state = search(state, testAction3);
        expect(state).toExist();
        expect(state.results).toEqual(["result3", "result4", "result5", "result6"]);
    });
    it('search results purge', () => {
        let state = search({
                results: ["result1", "result2"]
            }, {
                type: TEXT_SEARCH_RESULTS_PURGE,
                error: {message: "M"}
        });
        expect(state.results).toBe(null);
    });
    it('nested search service selected', () => {
        let state = search({
                results: ["result1", "result2"]
            }, {
                type: TEXT_SEARCH_NESTED_SERVICES_SELECTED,
                services: [{

                }],
                searchText: "TEST",
                selectedItems: [{
                    text: "text"
                }]

        });
        expect(state.selectedItems.length).toBe(1);
        expect(state.selectedServices.length).toBe(1);
        state = search(state, {
                type: TEXT_SEARCH_NESTED_SERVICES_SELECTED,
                services: [{

                }],
                searchText: "TEST",
                selectedItems: [{
                    text: "text"
                }]

        });
        expect(state.selectedItems.length).toBe(2);
        expect(state.selectedServices.length).toBe(1);
    });
    it('nested search cancel item', () => {
        let itemToCacel = {text: "text2"};
        let state = search({
                searchText: "",
                selectedItems: [{text: "text1"}, itemToCacel]
            }, {
                type: TEXT_SEARCH_CANCEL_ITEM,
                item: itemToCacel

        });
        expect(state.searchText).toBe("text2");
        expect(state.selectedItems.length).toBe(1);
    });
});
