/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

require('../assets/css/viewer.css');

const {connect} = require('react-redux');

const url = require('url');

const ConfigUtils = require('../../../utils/ConfigUtils');

const {loadMapConfig} = require('../../../actions/config');

const {resetControls} = require('../../../actions/controls');

const urlQuery = url.parse(window.location.href, true).query;

const PluginsContainer = connect((state) => ({
    pluginsConfig: state.plugins || ConfigUtils.getConfigProp('plugins') || null,
    mode: (urlQuery.mobile || (state.browser && state.browser.touch)) ? 'mobile' : 'desktop'
}))(require('../../../components/plugins/PluginsContainer'));


const MapViewer = React.createClass({
    propTypes: {
        mode: React.PropTypes.string,
        params: React.PropTypes.object,
        loadMapConfig: React.PropTypes.func,
        reset: React.PropTypes.func,
        plugins: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            mode: 'desktop'
        };
    },
    componentWillMount() {
        if (this.props.params.mapType && this.props.params.mapId) {

            const mapId = (this.props.params.mapId === '0') ? null : this.props.params.mapId;
            const config = urlQuery && urlQuery.config || null;
            const {configUrl} = ConfigUtils.getConfigurationOptions({mapId, config});
            this.props.reset();
            this.props.loadMapConfig(configUrl, mapId !== null);
        }
    },
    render() {
        return (<PluginsContainer key="viewer" id="viewer" className="viewer"
            plugins={this.props.plugins}
            params={this.props.params}
            />);
    }
});

module.exports = connect((state) => ({
    mode: (urlQuery.mobile || (state.browser && state.browser.touch)) ? 'mobile' : 'desktop'
}),
{
    loadMapConfig,
    reset: resetControls
})(MapViewer);
