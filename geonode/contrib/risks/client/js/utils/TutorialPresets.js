/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */


const riskTutorialPresets = {
    DATA_LOADED: [{
            translationHTML: 'riskSelector',
            selector: '#disaster-risk-selector-menu'
        },
        {
            translationHTML: 'riskOverview',
            selector: '#disaster-overview-list'
        },
        {
            translationHTML: 'riskMap',
            selector: '#disaster-map-main-container'
        },
        {
            translationHTML: 'riskNavigator',
            selector: '#disaster-navigation'
        },
        {
            translationHTML: 'riskPageTool',
            selector: '#disaster-page-tools'
        },
        {
            translationHTML: 'riskHelp',
            selector: '#disaster-show-tutorial'
        }
    ],
    DATA_LOADED_R: [{
            translationHTML: 'riskTab',
            selector: '#disaster-analysis-menu'
        },
        {
            translationHTML: 'riskList',
            selector: '#disaster-analysis-container'
        }
    ],
    ANALYSIS_DATA_LOADED: [{
            translationHTML: 'riskChart',
            selector: '#disaster-chart-container'
        },
        {
            translationHTML: 'riskLayer',
            selector: '#disaster-layer-button'
        },
        {
            translationHTML: 'riskInfo',
            selector: '#disaster-identify-button'
        },
        {
            translationHTML: 'riskUnit',
            selector: '#disaster-sub-units-button'
        },
        {
            translationHTML: 'riskSwitch',
            selector: '#disaster-switch-button'
        },
        {
            translationHTML: 'riskMapSlider',
            selector: '#disaster-map-slider'
        },
        {
            translationHTML: 'riskLegend',
            selector: '#disaster-map-legend'
        },
        {
            translationHTML: 'riskFurtherResources',
            selector: '#disaster-further-resources'
        },
        {
            translationHTML: 'riskMoreInfo',
            selector: '#disaster-more-info-button'
        },
        {
            translationHTML: 'riskDownloadData',
            selector: '#disaster-download-data-button'
        },
        {
            translationHTML: 'riskBack',
            selector: '#disaster-back-button'
        }
    ]
};

const costTutorialPresets = {
    DATA_LOADED: [{
            translationHTML: 'riskSelector',
            selector: '#disaster-risk-selector-menu'
        },
        {
            translationHTML: 'riskOverview',
            selector: '#disaster-overview-list'
        },
        {
            translationHTML: 'riskMap',
            selector: '#disaster-map-main-container'
        },
        {
            translationHTML: 'riskPageTool',
            selector: '#disaster-page-tools'
        },
        {
            translationHTML: 'riskHelp',
            selector: '#disaster-show-tutorial'
        }
    ],
    DATA_LOADED_R: [{
            translationHTML: 'riskTab',
            selector: '#disaster-analysis-menu'
        },
        {
            translationHTML: 'riskList',
            selector: '#disaster-analysis-container'
        }
    ],
    ANALYSIS_DATA_LOADED: [{
            translationHTML: 'costCompare',
            selector: '#disaster-compare-container'
        },
        {
            translationHTML: 'costChart',
            selector: '#disaster-chart-container'
        },
        {
            translationHTML: 'riskLayer',
            selector: '#disaster-layer-button'
        },
        {
            translationHTML: 'riskInfo',
            selector: '#disaster-identify-button'
        },
        {
            translationHTML: 'costMap',
            selector: '#viewer'
        },
        {
            translationHTML: 'riskLegend',
            selector: '#disaster-map-legend'
        },
        {
            translationHTML: 'costSwitch',
            selector: '#disaster-switch-chart-button'
        },
        {
            translationHTML: 'riskMoreInfo',
            selector: '#disaster-more-info-button'
        },
        {
            translationHTML: 'riskDownloadData',
            selector: '#disaster-download-data-button'
        },
        {
            translationHTML: 'riskBack',
            selector: '#disaster-back-button'
        }
    ]
};

const defaultStep = {
    title: '',
    text: '',
    position: 'bottom',
    type: 'click',
    allowClicksThruHole: true
};

module.exports = {
    defaultStep,
    riskTutorialPresets,
    costTutorialPresets
};
