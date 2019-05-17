/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const uuid = require('uuid');

const SET_VECTOR_RULE_PARAMETER = 'SET_VECTOR_RULE_PARAMETER';
const NEW_VECTOR_RULE = 'NEW_VECTOR_RULE';
const REMOVE_VECTOR_RULE = 'REMOVE_VECTOR_RULE';
const SELECT_VECTOR_RULE = 'SELECT_VECTOR_RULE';
const SET_VECTORSTYLE_PARAMETER = 'SET_VECTORSTYLE_PARAMETER';
const SET_VECTOR_LAYER = 'SET_VECTOR_LAYER';

function setVectorStyleParameter(component, property, value) {
    return {
        type: SET_VECTORSTYLE_PARAMETER,
        component,
        property,
        value
    };
}
function setVectorRuleParameter(property, value) {
    return {
        type: SET_VECTOR_RULE_PARAMETER,
        property,
        value
    };
}
function setVectorLayer(layer) {
    return {
        type: SET_VECTOR_LAYER,
        layer
    };
}
function newVectorRule() {
    return {
        type: NEW_VECTOR_RULE,
        id: uuid.v1()
    };
}
function removeVectorRule(id) {
    return {
        type: REMOVE_VECTOR_RULE,
        id
    };
}
function selectVectorRule(id) {
    return {
        type: SELECT_VECTOR_RULE,
        id
    };
}
module.exports = {
    NEW_VECTOR_RULE,
    REMOVE_VECTOR_RULE,
    SELECT_VECTOR_RULE,
    SET_VECTORSTYLE_PARAMETER,
    SET_VECTOR_RULE_PARAMETER,
    SET_VECTOR_LAYER,
    setVectorRuleParameter,
    setVectorStyleParameter,
    setVectorLayer,
    newVectorRule,
    removeVectorRule,
    selectVectorRule
};
