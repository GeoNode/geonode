/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const {connect} = require('react-redux');

const url = require('url');
const urlQuery = url.parse(window.location.href, true).query;

const ConfigUtils = require('../utils/ConfigUtils');
const PluginsUtils = require('../utils/PluginsUtils');

const PluginsContainer = connect((state) => ({
    pluginsConfig: state.plugins || ConfigUtils.getConfigProp('plugins') || null,
    mode: (urlQuery.mode || (state.browser && state.browser.mobile ? 'mobile' : 'desktop')),
    pluginsState: state && state.controls || {},
    monitoredState: PluginsUtils.filterState(state, ConfigUtils.getConfigProp('monitorState') || [])
}))(require('../components/plugins/PluginsContainer'));

const MapViewer = React.createClass({
    propTypes: {
        params: React.PropTypes.object,
        loadMapConfig: React.PropTypes.func,
        plugins: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            mode: 'desktop',
            loadMapConfig: () => {}
        };
    },
    componentWillMount() {
        this.props.loadMapConfig();
    },
    render() {
        return (<PluginsContainer key="viewer" id="viewer" className="viewer"
            plugins={this.props.plugins}
            params={this.props.params}
            />);
    }
});

module.exports = MapViewer;
