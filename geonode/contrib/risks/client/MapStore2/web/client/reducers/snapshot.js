/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var {CHANGE_SNAPSHOT_STATE, SNAPSHOT_ERROR, SNAPSHOT_READY, SNAPSHOT_ADD_QUEUE, SNAPSHOT_REMOVE_QUEUE} = require('../actions/snapshot');

const assign = require('object-assign');

function snapshot(state = null, action) {
    switch (action.type) {
        case CHANGE_SNAPSHOT_STATE:
            return assign({}, state, {
                state: action.state,
                tainted: action.tainted
            });
        case SNAPSHOT_READY:
            return assign({}, state, {
                img: {
                    data: action.imgData,
                    width: action.width,
                    height: action.height,
                    size: action.size
                }
            });
        case SNAPSHOT_ERROR:
            return assign({}, state, {
                error: action.error
            });
        case SNAPSHOT_ADD_QUEUE: {
            let queue = [];
            if (state && state.queue !== undefined) {
                queue = [...state.queue, action.options];
            } else {
                queue = [action.options];
            }
            return assign({}, state, {
                queue: queue
            });
        }
        case SNAPSHOT_REMOVE_QUEUE: {
            let queue = state.queue || [];
            queue = queue.filter((conf) => {
                if (conf.key === action.options.key) {
                    return false;
                }
                return true;
            });
            return assign({}, state, {
                queue: queue
            });
        }
        default:
            return state;
    }

}

module.exports = snapshot;
