/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const Undoable = require('redux-undo');
const assign = require('object-assign');

const mapConfigHistory = (reducer) => {
    return (state, action) => {
        let newState = reducer(state, action);
        let unredoState;
        // If undo modified the state we change mapStateSource
        if (action.type === Undoable.ActionTypes.UNDO && state.past.length > 0) {
            let mapC = assign({}, newState.present, {mapStateSource: "undoredo", style: state.present.style, resize: state.present.resize});
            unredoState = assign({}, newState, {present: mapC});
        }else if (action.type === Undoable.ActionTypes.REDO && state.future.length > 0) {
            let mapC = assign({}, newState.present, {mapStateSource: "undoredo", style: state.present.style, resize: state.present.resize});
            unredoState = assign({}, newState, {present: mapC});
        }
        return unredoState || newState;
    };
};

module.exports = mapConfigHistory;
