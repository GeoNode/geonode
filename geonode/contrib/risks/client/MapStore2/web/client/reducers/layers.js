/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

var {LAYER_LOADING, LAYER_LOAD, LAYER_ERROR, CHANGE_LAYER_PROPERTIES, CHANGE_GROUP_PROPERTIES,
    TOGGLE_NODE, SORT_NODE, REMOVE_NODE, UPDATE_NODE, ADD_LAYER, REMOVE_LAYER,
    SHOW_SETTINGS, HIDE_SETTINGS, UPDATE_SETTINGS, INVALID_LAYER
    } = require('../actions/layers');

var assign = require('object-assign');
var {isObject, isArray, head, isString} = require('lodash');

const LayersUtils = require('../utils/LayersUtils');

const deepChange = (nodes, findValue, propName, propValue) => {
    if (nodes && isArray(nodes) && nodes.length > 0) {
        return nodes.map((node) => {
            if (isObject(node)) {
                if (node.id === findValue) {
                    return assign({}, node, {[propName]: propValue});
                }else if (node.nodes) {
                    return assign({}, node, {nodes: deepChange(node.nodes, findValue, propName, propValue)});
                }
            }
            return node;
        });
    }
    return [];
};

/**
Removes a group even if it is nested
It works for layers too
**/
const deepRemove = (nodes, findValue) => {
    if (nodes && isArray(nodes) && nodes.length > 0) {
        return nodes.filter((node) => (node.id && node.id !== findValue) || (isString(node) && node !== findValue )).map((node) => isObject(node) ? assign({}, node, node.nodes ? {
            nodes: deepRemove(node.nodes, findValue)
        } : {}) : node);
    }
    return nodes;
};
const getNode = (nodes, id) => {
    if (nodes && isArray(nodes)) {
        return nodes.reduce((previous, node) => {
            if (previous) {
                return previous;
            }
            if (node && (node.name === id || node.id === id)) {
                return node;
            }
            if (node && node.nodes && node.nodes.length > 0) {
                return getNode(node.nodes, id);
            }
            return previous;
        }, null);
    }
    return null;
};

const moveNode = (groups, node, groupId, newLayers, foreground = true) => {
    // Remove node from old group
    let newGroups = deepRemove(groups, node);
    // Check if group to move to exists
    let group = getNode(newGroups, groupId);
    if (!group) {
        // Create missing group
        group = head(LayersUtils.getLayersByGroup([getNode(newLayers, node)]));
        // check for parent group if exist
        const parentGroup = groupId.split('.').reduce((tree, gName, idx) => {
            const gId = groupId.split(".", idx + 1).join('.');
            const parent = getNode(newGroups, gId);
            return parent ? tree.concat(parent) : tree;
        }, []).pop();
        if (parentGroup) {
            group = getNode([group], parentGroup.id).nodes[0];
            newGroups = deepChange(newGroups, parentGroup.id, 'nodes', foreground ? [group].concat(parentGroup.nodes) : parentGroup.nodes.concat(group));
        }else {
            newGroups = [group].concat(newGroups);
        }
    }else {
        newGroups = deepChange(newGroups, group.id, 'nodes', foreground ? [node].concat(group.nodes.slice(0)) : group.nodes.concat(node));
    }
    return LayersUtils.removeEmptyGroups(newGroups);
};

function layers(state = [], action) {
    switch (action.type) {
        case LAYER_LOADING: {
            const newLayers = (state.flat || []).map((layer) => {
                return layer.id === action.layerId ? assign({}, layer, {loading: true, loadingError: false}) : layer;
            });
            return assign({}, state, {flat: newLayers});
        }
        case LAYER_LOAD: {
            const newLayers = (state.flat || []).map((layer) => {
                return layer.id === action.layerId ? assign({}, layer, {loading: false, loadingError: action.error ? "Error" : false}) : layer;
            });
            return assign({}, state, {flat: newLayers});
        }
        case LAYER_ERROR: {
            const newLayers = (state.flat || []).map((layer) => {
                return layer.id === action.layerId ? assign({}, layer, {loading: false, loadingError: true}) : layer;
            });
            return assign({}, state, {flat: newLayers});
        }
        case CHANGE_LAYER_PROPERTIES: {
            const flatLayers = (state.flat || []);
            let isBackground = flatLayers.reduce(
                    (background, layer) => background || (layer.id === action.layer && layer.group === 'background'),
            false);
            const newLayers = flatLayers.map((layer) => {
                if (layer.id === action.layer) {
                    return assign({}, layer, action.newProperties);
                } else if (layer.group === 'background' && isBackground && action.newProperties.visibility) {
                    // TODO remove
                    return assign({}, layer, {visibility: false});
                }
                return assign({}, layer);
            });
            return assign({}, state, {flat: newLayers});
        }
        case CHANGE_GROUP_PROPERTIES: {
            let newLayers = state.flat.map((layer) => {
                const layerGroup = layer.group || 'Default';
                if (layerGroup === action.group || layerGroup.indexOf(`${action.group}.`) === 0) {
                    return assign({}, layer, action.newProperties);
                }
                return assign({}, layer);
            });
            return assign({}, state, {
                flat: newLayers
            });
        }
        case TOGGLE_NODE: {
            let nodeSelector = action.nodeType === 'layers' ? 'flat' : 'groups';
            let nodes = state[nodeSelector] || [];
            const newNodes = deepChange(nodes, action.node, 'expanded', action.status);
            return assign({}, state, {[nodeSelector]: newNodes});
        }
        case SORT_NODE: {
            let node = getNode(state.groups || [], action.node);
            let nodes = node && node.nodes || action.node === 'root' && state.groups || null;
            if (nodes) {
                let reorderedNodes = action.order.map((idx) => {
                    return nodes[idx];
                });
                const newNodes = action.node === 'root' ? reorderedNodes :
                    deepChange(state.groups, action.node, 'nodes', reorderedNodes);
                let newLayers = action.sortLayers ? action.sortLayers(newNodes, state.flat) : state.flat;
                return assign({}, state, {groups: newNodes, flat: newLayers});
            }
        }
        case UPDATE_NODE: {
            const flatLayers = (state.flat || []);
            const selector = action.nodeType === 'groups' ? 'group' : 'id';

            // const newGroups = action.options && action.options.group && action.options.group !== layer;
            let sameGroup = action.options.hasOwnProperty("group") ? false : true;

            const newLayers = flatLayers.map((layer) => {
                if (layer[selector] === action.node || layer[selector].indexOf(action.node + '.') === 0) {
                    if (layer.group === (action.options.group || 'Default')) {
                        // If the layer didn't change group, raise a flag to prevent groups update
                        sameGroup = true;
                    }
                    // Edit the layer with the new options
                    return assign({}, layer, action.options);
                }
                return assign({}, layer);
            });
            let originalNode = head(flatLayers.filter((layer) => { return (layer[selector] === action.node || layer[selector].indexOf(action.node + '.') === 0); }));
            if (!sameGroup && originalNode ) {
                // Remove layers from old group
                const groupId = (action.options.group || 'Default');
                const newGroups = moveNode(state.groups, action.node, groupId, newLayers);

                let orderedNewLayers = LayersUtils.sortLayers ? LayersUtils.sortLayers(newGroups, newLayers) : newLayers;
                return assign({}, state, {
                    flat: orderedNewLayers,
                    groups: newGroups
                });
            }
            return assign({}, state, {flat: newLayers});
        }
        case INVALID_LAYER: {
            const flatLayers = (state.flat || []);

            const newLayers = flatLayers.map((layer) => {
                if (layer.id === action.options.id) {
                    return assign({}, layer, {invalid: true});
                }
                return assign({}, layer);
            });
            return assign({}, state, {flat: newLayers});
        }
        case REMOVE_NODE: {
            if (action.nodeType === 'groups') {
                const newGroups = deepRemove(state.groups, action.node);
                const newLayers = state.flat.filter((layer) => layer.group !== action.node && layer.group.indexOf(action.node + '.') !== 0);

                return {
                    flat: newLayers,
                    groups: newGroups
                };
            }
            if (action.nodeType === 'layers') {
                const newGroups = deepRemove(state.groups, action.node);
                const newLayers = state.flat.filter((layer) => layer.id !== action.node);
                return assign({}, state, {
                    flat: newLayers,
                    groups: newGroups
                });
            }
        }
        case ADD_LAYER: {
            let newLayers = (state.flat || []).concat();
            let newGroups = (state.groups || []).concat();
            const newLayer = (action.layer.id) ? action.layer : assign({}, action.layer, {id: LayersUtils.getLayerId(action.layer, newLayers)});
            newLayers.push(newLayer);
            const groupId = newLayer.group || 'Default';
            if (groupId !== "background") {
                newGroups = moveNode(newGroups, newLayer.id, groupId, newLayers, action.foreground);
            }
            let orderedNewLayers = LayersUtils.sortLayers ? LayersUtils.sortLayers(newGroups, newLayers) : newLayers;
            return {
                    flat: orderedNewLayers,
                    groups: newGroups
            };
        }
        case REMOVE_LAYER: {
            const newGroups = deepRemove(state.groups, action.layerId);
            const newLayers = state.flat.filter((layer) => layer.id !== action.layerId);
            return assign({}, state, {
                flat: newLayers,
                groups: newGroups
            });
        }
        case SHOW_SETTINGS: {
            let settings = assign({}, state.settings, {
                expanded: true,
                node: action.node,
                nodeType: action.nodeType,
                options: action.options
            });
            return assign({}, state, {
                settings: settings
            });
        }
        case HIDE_SETTINGS: {
            let settings = assign({}, state.Settings, {
                expanded: false,
                node: null,
                nodeType: null,
                options: {}
            });
            return assign({}, state, {
                settings: settings
            });
        }
        case UPDATE_SETTINGS: {
            const options = assign({},
                state.settings && state.settings.options,
                action.options
            );
            const settings = assign({}, state.settings, {options: options});
            return assign({}, state, {
                settings: settings
            });
        }
        default:
            return state;
    }
}

module.exports = layers;
