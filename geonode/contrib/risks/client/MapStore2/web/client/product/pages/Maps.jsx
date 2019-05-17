/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

require("../assets/css/maps.css");

const {connect} = require('react-redux');

const url = require('url');
const urlQuery = url.parse(window.location.href, true).query;

const ConfigUtils = require('../../utils/ConfigUtils');

const {loadMapConfig} = require('../../actions/config');
const {resetControls} = require('../../actions/controls');

const Page = require('../../containers/Page');

const MapsPage = React.createClass({
    propTypes: {
        name: React.PropTypes.string,
        mode: React.PropTypes.string,
        params: React.PropTypes.object,
        loadMaps: React.PropTypes.func,
        reset: React.PropTypes.func,
        plugins: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            name: "maps",
            mode: 'desktop',
            loadMaps: () => {},
            reset: () => {}
        };
    },
    componentWillMount() {
        if (this.props.params.mapType && this.props.params.mapId) {
            if (this.props.mode === 'mobile') {
                require('../assets/css/mobile.css');
            }
            this.props.reset();
            this.props.loadMaps(ConfigUtils.getDefaults().geoStoreUrl, ConfigUtils.getDefaults().initialMapFilter || "*");
        }
    },
    render() {
        let plugins = ConfigUtils.getConfigProp("plugins") || {};
        let pagePlugins = {
            "desktop": plugins.common || [],// TODO mesh page plugins with other plugins
            "mobile": plugins.common || []
        };
        let pluginsConfig = {
            "desktop": plugins[this.props.name] || [],// TODO mesh page plugins with other plugins
            "mobile": plugins[this.props.name] || []
        };

        return (<Page
            id="maps"
            pagePluginsConfig={pagePlugins}
            pluginsConfig={pluginsConfig}
            plugins={this.props.plugins}
            params={this.props.params}
            />);
    }
});

module.exports = connect((state) => ({
    mode: (urlQuery.mobile || (state.browser && state.browser.mobile)) ? 'mobile' : 'desktop'
}),
{
    loadMapConfig,
    reset: resetControls
})(MapsPage);
