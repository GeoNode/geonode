/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');

const PluginsUtils = require('../../utils/PluginsUtils');

const assign = require('object-assign');

const {get} = require('lodash');

const PluginsContainer = React.createClass({
    propTypes: {
        mode: React.PropTypes.string,
        params: React.PropTypes.object,
        plugins: React.PropTypes.object,
        pluginsConfig: React.PropTypes.object,
        id: React.PropTypes.string,
        className: React.PropTypes.string,
        style: React.PropTypes.object,
        pluginsState: React.PropTypes.object,
        monitoredState: React.PropTypes.object,
        defaultMode: React.PropTypes.string
    },
    getDefaultProps() {
        return {
            mode: 'desktop',
            defaultMode: 'desktop',
            params: {},
            plugins: {},
            pluginsConfig: {},
            id: "plugins-container",
            className: "plugins-container",
            style: {},
            pluginsState: {},
            monitoredState: {}
        };
    },
    getInitialState() {
        return {
            loadedPlugins: {}
        };
    },
    componentWillMount() {
        this.loadPlugins(this.props.pluginsState);
    },
    componentWillReceiveProps(newProps) {
        this.loadPlugins(newProps.pluginsState);
    },
    getState(path) {
        return get(this.props.monitoredState, path) || get(this.props.params, path);
    },
    getPluginDescriptor(plugin) {
        return PluginsUtils.getPluginDescriptor(this.getState, this.props.plugins,
                    this.props.pluginsConfig[this.props.mode], plugin, this.state.loadedPlugins);
    },
    renderPlugins(plugins) {
        return plugins
            .filter((Plugin) => !Plugin.hide)
            .map(this.getPluginDescriptor)
            .filter((Plugin) => !Plugin.impl.loadPlugin)
            .filter(this.filterPlugins)
            .map((Plugin) => <Plugin.impl key={Plugin.id}
                {...this.props.params} {...Plugin.cfg} items={Plugin.items}/>);
    },
    render() {
        if (this.props.pluginsConfig) {
            return (
                <div id={this.props.id} className={this.props.className} style={this.props.style}>
                    {
                     this.props.pluginsConfig[this.props.mode] ? this.renderPlugins(this.props.pluginsConfig[this.props.mode]) : this.props.pluginsConfig[this.props.defaultMode]
                    }
                </div>
            );
        }
        return null;
    },
    filterPlugins(Plugin) {
        const container = PluginsUtils.getMorePrioritizedContainer(Plugin.impl, this.props.pluginsConfig[this.props.mode], 0);
        return !container.plugin || !container.plugin.impl || container.plugin.impl.doNotHide;
    },
    loadPlugins(state) {
        (this.props.pluginsConfig && this.props.pluginsConfig[this.props.mode] || [])
            .map((plugin) => PluginsUtils.getPluginDescriptor(this.getState, this.props.plugins,
                this.props.pluginsConfig[this.props.mode], plugin, this.state.loadedPlugins))
            .filter((plugin) => plugin.impl.loadPlugin).forEach((plugin) => {
                if (!this.state.loadedPlugins[plugin.name]) {
                    if (!plugin.impl.enabler || plugin.impl.enabler(state)) {
                        plugin.impl.loadPlugin((impl) => this.loadPlugin(plugin, impl));
                    }
                }
            });
    },
    loadPlugin(plugin, impl) {
        this.setState({
            loadedPlugins: assign({}, this.state.loadedPlugins, {[plugin.name]: impl})
        });
    }
});

module.exports = PluginsContainer;
