/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {
    NEW_VECTOR_RULE,
    SELECT_VECTOR_RULE,
    REMOVE_VECTOR_RULE,
    SET_VECTORSTYLE_PARAMETER,
    SET_VECTOR_LAYER,
    SET_VECTOR_RULE_PARAMETER
} = require('../actions/vectorstyler');
const { STYLER_RESET } = require('../actions/styler');
const assign = require('object-assign');
const {isObject, findIndex} = require('lodash');
const baseStyle = {
    Point: {
            type: "Point",
            color: { r: 0, g: 0, b: 255, a: 1 },
            width: 3,
            fill: { r: 0, g: 0, b: 255, a: 0.1 },
            radius: 10,
            marker: false,
            markName: "circle"
            },
    Line: {
            type: "Line",
            color: { r: 0, g: 0, b: 255, a: 1 },
            width: 3
            },
    Polygon: {
            type: "Polygon",
            color: { r: 0, g: 0, b: 255, a: 1 },
            width: 3,
            fill: { r: 0, g: 0, b: 255, a: 0.1 }
    }

};

const initialSpec = {
        rules: []
};
function getType(layer) {
    switch (layer.describeLayer.geometryType) {
        case 'Polygon':
        case 'MultiPolygon': {
            return "Polygon";
        }
        case 'MultiLineString':
        case 'LineString': {
            return "Line";
        }
        case 'Point':
        case 'MultiPoint': {
            return "Point";
        }
        default: {
            return "Polygon";
        }
    }
}

function getBaseSymbol(type = "Polygon") {
    let newSymbol = {};
    let symbol = baseStyle[type];
    Object.keys(symbol).reduce((pr, next) => {
        pr[next] = isObject(symbol[next]) ? assign({}, symbol[next]) : symbol[next];
        return pr;
    }, newSymbol);
    return newSymbol;
}

function getRuleIdx(rules, id) {
    return findIndex(rules, (r) => {return r.id === id; });
}

function vectorstyler(state = initialSpec, action) {
    switch (action.type) {
        case NEW_VECTOR_RULE: {
            const newRule = {
                id: action.id,
                symbol: getBaseSymbol(getType(state.layer)),
                name: 'New Rule'
            };

            return assign({}, state, {rule: newRule.id, rules: (state.rules ? [...state.rules, newRule] : [newRule])});

        }
        case SELECT_VECTOR_RULE: {
            return assign({}, state, {rule: action.id});

        }
        case REMOVE_VECTOR_RULE: {
            const idx = getRuleIdx(state.rules, action.id);
            let newSelected = (state.rules[idx - 1]) ? state.rules[idx - 1].id : undefined;
            if (newSelected === undefined) {
                newSelected = (state.rules[idx + 1]) ? state.rules[idx + 1].id : undefined;
            }
            return assign({}, state, {rule: newSelected, rules: state.rules.filter((rule) => rule.id !== action.id)});
        }
        case SET_VECTOR_RULE_PARAMETER: {
            let newRules = state.rules.slice();
            const ruleIdx = getRuleIdx(newRules, state.rule);
            const activeRule = newRules[ruleIdx];
            newRules[ruleIdx] = assign({}, activeRule, {[action.property]: action.value});
            return assign({}, state, {rules: newRules});
        }
        case SET_VECTORSTYLE_PARAMETER: {
            let newRules = state.rules.slice();
            const ruleIdx = getRuleIdx(newRules, state.rule);
            const activeRule = newRules[ruleIdx];
            newRules[ruleIdx] = assign( {}, activeRule, {
                [action.component]: assign({}, activeRule[action.component], {
                    [action.property]: action.value
                })
            });
            return assign({}, state, {rules: newRules});

        }
        case SET_VECTOR_LAYER: {
            return assign({}, initialSpec, { layer: action.layer});
        }
        case STYLER_RESET: {
            return initialSpec;
        }
        default:
            return state;
    }
}

module.exports = vectorstyler;
