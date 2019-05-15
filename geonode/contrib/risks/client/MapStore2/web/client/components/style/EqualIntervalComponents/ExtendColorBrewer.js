/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const extendColorBrewer = {
    Earth: {
    3: ["#3e2f8d", "#d3e1b2", "#f1e8dd"],
    4: ["#3e2f8d", "#a4cef4", "#676c52", "#f1e8dd"],
    5: ["#3e2f8d", "#87b2f1", "#d3e1b2", "#615742", "#f1e8dd"],
    6: ["#3e2f8d", "#739cd3", "#cbe1da", "#8e9f79", "#7e6d4f", "#f1e8dd"],
    7: ["#3e2f8d", "#6a8dc7", "#a4cef4", "#d3e1b2", "#676c52", "#89795d", "#f1e8dd"],
    8: ["#3e2f8d", "#6783c7", "#94c0fb", "#e1e9ca", "#a3b990", "#524d3d", "#908169", "#f1e8dd"],
    9: ["#3e2f8d", "#657bc7", "#87b2f1", "#b9dae8", "#d3e1b2", "#7b8965", "#615742", "#948671", "#f1e8dd"],
    10: ["#3e2f8d", "#6375c7", "#7ca6e0", "#a4cef4", "#eceec1", "#afc79c", "#676c52", "#716349", "#988b78", "#f1e8dd"],
    11: ["#3e2f8d", "#6271c7", "#739cd3", "#99c4f9", "#cbe1da", "#d3e1b2", "#8e9f79", "#585743", "#7e6d4f", "#9b8f7e", "#f1e8dd"],
    12: ["#3e2f8d", "#616dc7", "#6c93c7", "#8fbcfe", "#aed6f1", "#f1f0be", "#bbd5a9", "#788562", "#504a3b", "#847252", "#9b8f7e", "#f1e8dd"]
    },
    Land: {
    3: ["#c3e2df", "#2f412c", "#e7e9dd"],
    4: ["#c3e2df", "#5d7a65", "#3f3633", "#e7e9dd"],
    5: ["#c3e2df", "#868f65", "#2f412c", "#5c4e4b", "#e7e9dd"],
    6: ["#c3e2df", "#979f72", "#446553", "#302f26", "#6e5d56", "#e7e9dd"],
    7: ["#c3e2df", "#a5ac7d", "#5d7a65", "#2f412c", "#3f3633", "#7b695a", "#e7e9dd"],
    8: ["#c3e2df", "#b0b788", "#768562", "#3c5a46", "#2d3123", "#4f4342", "#84715c", "#e7e9dd"],
    9: ["#c3e2df", "#b8c091", "#868f65", "#4b6e5f", "#2f412c", "#322d28", "#5c4e4b", "#8c775d", "#e7e9dd"],
    10: ["#c3e2df", "#bfc697", "#8f986c", "#5d7a65", "#37553e", "#2b3221", "#3f3633", "#665651", "#917c5e", "#e7e9dd"],
    11: ["#c3e2df", "#c4cc9d", "#979f72", "#6f8263", "#446553", "#2f412c", "#302f26", "#4a3f3d", "#6e5d56", "#96805f", "#e7e9dd"],
    12: ["#c3e2df", "#c8d0a1", "#9ea576", "#7d8861", "#4e7265", "#35513a", "#2a3320", "#352e2a", "#534745", "#756359", "#9d896a", "#e7e9dd"]
    },
    Water: {
    3: ["#1f373d", "#4cc1b2", "#dee2b6"],
    4: ["#1f373d", "#309590", "#85dfce", "#dee2b6"],
    5: ["#1f373d", "#2a8180", "#4cc1b2", "#a1f3dc", "#dee2b6"],
    6: ["#1f373d", "#2f6f79", "#30a8a2", "#76d1c6", "#c1fdf6", "#dee2b6"],
    7: ["#1f373d", "#306573", "#309590", "#4cc1b2", "#85dfce", "#c8f3dc", "#dee2b6"],
    8: ["#1f373d", "#305f6b", "#2a8b86", "#2fb2aa", "#6eccbd", "#8deccd", "#c8e6bb", "#dee2b6"],
    9: ["#1f373d", "#2f5b66", "#2a8180", "#32a09a", "#4cc1b2", "#7dd5ce", "#a1f3dc", "#c8dda3", "#dee2b6"],
    10: ["#1f373d", "#2f5862", "#2d777c", "#309590", "#2eb8af", "#69cab8", "#85dfce", "#b3f8eb", "#c8d690", "#dee2b6"],
    11: ["#1f373d", "#2f555f", "#2f6f79", "#2c8e89", "#30a8a2", "#4cc1b2", "#76d1c6", "#8ae8cd", "#c1fdf6", "#c8d181", "#dee2b6"],
    12: ["#1f373d", "#2f535c", "#306977", "#298883", "#329c97", "#30bab1", "#66c8b4", "#80d7cf", "#92efd0", "#c8faf0", "#cad285", "#dee2b6"]
    },
    CDA: {
    3: ["#18c6ca", "#fed873", "#ffffff"],
    4: ["#18c6ca", "#fffbc3", "#e3ce9b", "#ffffff"],
    5: ["#18c6ca", "#e9feb4", "#fed873", "#d0c6b0", "#ffffff"],
    6: ["#18c6ca", "#cffea9", "#fef5af", "#efd28b", "#c8c2b6", "#ffffff"],
    7: ["#18c6ca", "#bafea1", "#fffbc3", "#fed873", "#e3ce9b", "#ccc8c1", "#ffffff"],
    8: ["#18c6ca", "#affe9d", "#f0feb8", "#fef3a8", "#f3d486", "#d8c9a8", "#d3d0ca", "#ffffff"],
    9: ["#18c6ca", "#affe9d", "#e9feb4", "#fef7b5", "#fed873", "#e7cf96", "#d0c6b0", "#dad8d2", "#ffffff"],
    10: ["#18c6ca", "#a3fe9a", "#d8feac", "#fffbc3", "#feee9b", "#f7d580", "#e3ce9b", "#ccc4b3", "#dad8d2", "#ffffff"],
    11: ["#18c6ca", "#97fe96", "#cffea9", "#f7febb", "#fef5af", "#fed873", "#efd28b", "#dccaa4", "#c8c2b6", "#e1dfdb", "#ffffff"],
    12: ["#18c6ca", "#97fe96", "#c5fea5", "#f0feb8", "#fef9bc", "#feee9b", "#f7d580", "#e7cf96", "#d8c9a8", "#c4c1b9", "#e1dfdb", "#ffffff"]
    },
    Simple: {
    3: ["#000000", "#7fff00", "#bf7f3f"],
    4: ["#000000", "#38ff38", "#ffd400", "#bf7f3f"],
    5: ["#000000", "#7fff7f", "#7fff00", "#ff9f00", "#bf7f3f"],
    6: ["#000000", "#aaffaa", "#00ff00", "#ffff00", "#ff7f00", "#bf7f3f"],
    7: ["#000000", "#8dd48d", "#38ff38", "#7fff00", "#ffd400", "#f47f0a", "#bf7f3f"]
    }
};

const assign = require('object-assign');

module.exports = assign({}, require("colorbrewer"), extendColorBrewer);
