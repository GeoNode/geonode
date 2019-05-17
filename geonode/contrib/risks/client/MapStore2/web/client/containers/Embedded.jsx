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
const PluginsUtils = require('../utils/PluginsUtils');
const ConfigUtils = require('../utils/ConfigUtils');

const PluginsContainer = connect((state) => ({
    mode: (urlQuery.mode || (state.browser && state.browser.mobile ? 'mobile' : 'desktop')),
    pluginsState: state && state.controls || {},
    monitoredState: PluginsUtils.filterState(state, ConfigUtils.getConfigProp('monitorState') || [])
}))(require('../components/plugins/PluginsContainer'));

const Embedded = React.createClass({
    propTypes: {
        params: React.PropTypes.object,
        plugins: React.PropTypes.object,
        pluginsConfig: React.PropTypes.object
    },
    getDefaultProps() {
        return {
            mode: 'desktop',
            pluginsConfig: {
                desktop: [],
                mobile: []
            }
        };
    },
    render() {
        return (<PluginsContainer key="embedded" id="mapstore2-embedded" className="mapstore2-embedded"
            pluginsConfig={this.props.pluginsConfig}
            plugins={this.props.plugins}
            params={this.props.params}
            />);
    }
});

module.exports = Embedded;
