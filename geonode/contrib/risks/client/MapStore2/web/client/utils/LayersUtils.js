/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const assign = require('object-assign');
const {isObject, isArray, head} = require('lodash');

const getGroup = (groupId, groups) => {
    return head(groups.filter((subGroup) => isObject(subGroup) && subGroup.id === groupId));
};
const getLayer = (layerName, allLayers) => {
    return head(allLayers.filter((layer) => layer.id === layerName));
};
const getLayersId = (groupId, allLayers) => {
    return allLayers.filter((layer) => (layer.group || 'Default') === groupId).map((layer) => layer.id).reverse();
};
const initialReorderLayers = (groups, allLayers) => {
    return groups.slice(0).reverse().reduce((previous, group) => {
        return previous.concat(
            group.nodes.slice(0).reverse().reduce((layers, node) => {
                if (isObject(node)) {
                    return layers.concat(initialReorderLayers([node], allLayers));
                }
                return layers.concat(getLayer(node, allLayers));
            }, [])
            );
    }, []);
};
const reorderLayers = (groups, allLayers) => {
    return initialReorderLayers(groups, allLayers);
};
const createGroup = (groupId, groupName, layers, addLayers) => {
    return assign({}, {
            id: groupId,
            title: (groupName || "").replace(/\${dot}/g, "."),
            name: groupName,
            nodes: addLayers ? getLayersId(groupId, layers) : [],
            expanded: true
        });
};

var LayersUtils = {
    getLayerId: (layerObj, layers) => {
        return layerObj && layerObj.id || (layerObj.name + "__" + layers.length);
    },
    getLayersByGroup: (configLayers) => {
        let i = 0;
        let mapLayers = configLayers.map((layer) => assign({}, layer, {storeIndex: i++}));
        let groupNames = mapLayers.reduce((groups, layer) => {
            return groups.indexOf(layer.group || 'Default') === -1 ? groups.concat([layer.group || 'Default']) : groups;
        }, []).filter((group) => group !== 'background').reverse();

        return groupNames.reduce((groups, names)=> {
            let name = names || 'Default';
            name.split('.').reduce((subGroups, groupName, idx, array)=> {
                const groupId = name.split(".", idx + 1).join('.');
                let group = getGroup(groupId, subGroups);
                const addLayers = (idx === array.length - 1);
                if (!group) {
                    group = createGroup(groupId, groupName, mapLayers, addLayers);
                    subGroups.push(group);
                }else if (addLayers) {
                    group.nodes = group.nodes.concat(getLayersId(groupId, mapLayers));
                }
                return group.nodes;
            }, groups);
            return groups;
        }, []);
    },
    removeEmptyGroups: (groups) => {
        return groups.reduce((acc, group) => {
            return acc.concat(LayersUtils.getNotEmptyGroup(group));
        }, []);
    },
    getNotEmptyGroup: (group) => {
        const nodes = group.nodes.reduce((gNodes, node) => {
            return node.nodes ? gNodes.concat(LayersUtils.getNotEmptyGroup(node)) : gNodes.concat(node);
        }, []);
        return nodes.length > 0 ? assign({}, group, {nodes: nodes}) : [];
    },
    reorder: (groups, allLayers) => {
        return allLayers.filter((layer) => layer.group === 'background')
            .concat(reorderLayers(groups, allLayers));
    },
    denormalizeGroups: (allLayers, groups) => {
        let getGroupVisibility = (nodes) => {
            let visibility = true;
            nodes.forEach((node) => {
                if (!node.visibility) {
                    visibility = false;
                }
            });
            return visibility;
        };
        let getNormalizedGroup = (group, layers) => {
            const nodes = group.nodes.map((node) => {
                if (isObject(node)) {
                    return getNormalizedGroup(node, layers);
                }
                return layers.filter((layer) => layer.id === node)[0];
            });
            return assign({}, group, {nodes, visibility: getGroupVisibility(nodes)});
        };
        let normalizedLayers = allLayers.map((layer) => assign({}, layer, {expanded: layer.expanded || false}));
        return {
            flat: normalizedLayers,
            groups: groups.map((group) => getNormalizedGroup(group, normalizedLayers))
        };
    },

    sortLayers: (groups, allLayers) => {
        return allLayers.filter((layer) => layer.group === 'background')
            .concat(reorderLayers(groups, allLayers));
    },
    toggleByType: (type, toggleFun) => {
        return (node, status) => {
            return toggleFun(node, type, status);
        };
    },
    sortUsing: (sortFun, action) => {
        return (node, reorder) => {
            return action(node, reorder, sortFun);
        };
    },
    splitMapAndLayers: (mapState) => {
        if (mapState && isArray(mapState.layers)) {
            const groups = LayersUtils.getLayersByGroup(mapState.layers);
            return assign({}, mapState, {
                layers: {
                    flat: LayersUtils.reorder(groups, mapState.layers),
                    groups: groups
                }
            });
        }
        return mapState;
    },
    geoJSONToLayer: (geoJSON, id) => {
        return {
            type: 'vector',
            visibility: true,
            group: 'Local shape',
            id,
            name: geoJSON.fileName,
            hideLoading: true,
            features: geoJSON.features.map((feature, idx) => {
                if (!feature.id) {
                    feature.id = idx;
                }
                if (feature.geometry && feature.geometry.bbox && isNaN(feature.geometry.bbox[0])) {
                    feature.geometry.bbox = [null, null, null, null];
                }
                return feature;
            })
        };
    },
    saveLayer: (layer) => {
        return {
            features: layer.features,
            format: layer.format,
            group: layer.group,
            search: layer.search,
            source: layer.source,
            name: layer.name,
            opacity: layer.opacity,
            provider: layer.provider,
            styles: layer.styles,
            style: layer.style,
            availableStyles: layer.availableStyles,
            capabilitiesURL: layer.capabilitiesURL,
            title: layer.title,
            transparent: layer.transparent,
            type: layer.type,
            url: layer.url,
            bbox: layer.bbox,
            visibility: layer.visibility,
            singleTile: layer.singleTile || false,
            allowedSRS: layer.allowedSRS,
            matrixIds: layer.matrixIds,
            tileMatrixSet: layer.tileMatrixSet,
            ...assign({}, layer.params ? {params: layer.params} : {})
        };
    }

};

module.exports = LayersUtils;
