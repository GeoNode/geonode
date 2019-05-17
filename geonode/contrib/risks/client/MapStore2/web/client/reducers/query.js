/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {
    FEATURE_TYPE_SELECTED,
    FEATURE_TYPE_LOADED,
    FEATURE_TYPE_ERROR,
    FEATURE_LOADED,
    FEATURE_ERROR,
    QUERY_CREATE,
    QUERY_RESULT,
    QUERY_ERROR,
    RESET_QUERY,
    FEATURE_CLOSE
} = require('../actions/wfsquery');

const {QUERY_FORM_RESET} = require('../actions/queryform');
const {RESET_CONTROLS} = require('../actions/controls');

const assign = require('object-assign');

const types = {
    'xsd:string': 'string',
    'xsd:dateTime': 'date',
    'xsd:number': 'number',
    'xsd:int': 'number'
};
const fieldConfig = {};
const extractInfo = (featureType) => {
    return {
        attributes: featureType.featureTypes[0].properties
            .filter((attribute) => attribute.type.indexOf('gml:') !== 0)
            .map((attribute) => {
                let conf = {
                    label: attribute.name,
                    attribute: attribute.name,
                    type: types[attribute.type],
                    valueId: "id",
                    valueLabel: "name",
                    values: []
                };
                conf = fieldConfig[attribute.name] ? {...conf, ...fieldConfig[attribute.name]} : conf;
                return conf;
            })
    };
};

const extractData = (feature) => {
    return ['STATE_NAME', 'STATE_ABBR', 'SUB_REGION', 'STATE_FIPS' ].map((attribute) => ({
        attribute,
        values: feature.features.reduce((previous, current) => {
            if (previous.indexOf(current.properties[attribute]) === -1) {
                return [...previous, current.properties[attribute]].sort();
            }
            return previous;
        }, [])
    })).reduce((previous, current) => {
        return assign(previous, {
            [current.attribute]: current.values.map((value) => ({
                id: value,
                name: value
            }))
        });
    }, {});
};

const initialState = {
    featureTypes: {},
    data: {},
    result: null,
    resultError: null
};

function query(state = initialState, action) {
    switch (action.type) {
        case FEATURE_TYPE_SELECTED: {
            return assign({}, state, {
                typeName: action.typeName,
                url: action.url
            });
        }
        case FEATURE_TYPE_LOADED: {
            return assign({}, state, {
                featureTypes: assign({}, state.featureTypes, {[action.typeName]: extractInfo(action.featureType)})
            });
        }
        case FEATURE_TYPE_ERROR: {
            return assign({}, state, {
                featureTypes: assign({}, state.featureTypes, {[action.typeName]: {error: action.error}})
            });
        }
        case FEATURE_LOADED: {
            return assign({}, state, {
                data: assign({}, state.data, {[action.typeName]: extractData(action.feature)})
            });
        }
        case FEATURE_ERROR: {
            return assign({}, state, {
                featureTypes: assign({}, state.data, {[action.typeName]: {error: action.error}})
            });
        }
        case QUERY_CREATE: {
            return assign({}, state, {
                open: true,
                isNew: true,
                searchUrl: action.searchUrl,
                filterObj: action.filterObj
            });
        }
        case QUERY_RESULT: {
            return assign({}, state, {
                isNew: false,
                result: action.result,
                searchUrl: action.searchUrl,
                filterObj: action.filterObj,
                resultError: null
            });
        }
        case QUERY_ERROR: {
            return assign({}, state, {
                isNew: false,
                result: null,
                resultError: action.error
            });
        }
        case RESET_CONTROLS:
        case QUERY_FORM_RESET:
            return assign({}, state, {
                open: false,
                isNew: false,
                result: null,
                filterObj: null,
                searchUrl: null
            });
        case RESET_QUERY: {
            return assign({}, state, {
                result: null,
                resultError: null
            });
        }
        case FEATURE_CLOSE: {
            return assign({}, state, {
                open: false
            });
        }
        default:
            return state;
    }
}

module.exports = query;
