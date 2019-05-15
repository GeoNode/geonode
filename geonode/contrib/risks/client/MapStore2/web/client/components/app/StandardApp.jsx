/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const {Provider} = require('react-redux');

const {changeBrowserProperties} = require('../../actions/browser');
const {loadLocale} = require('../../actions/locale');
const {localConfigLoaded} = require('../../actions/localConfig');
const {loadPrintCapabilities} = require('../../actions/print');

const ConfigUtils = require('../../utils/ConfigUtils');
const LocaleUtils = require('../../utils/LocaleUtils');
const PluginsUtils = require('../../utils/PluginsUtils');

const assign = require('object-assign');
const url = require('url');

const urlQuery = url.parse(window.location.href, true).query;

const StandardApp = React.createClass({
    propTypes: {
        appStore: React.PropTypes.func,
        pluginsDef: React.PropTypes.object,
        storeOpts: React.PropTypes.object,
        initialActions: React.PropTypes.array,
        appComponent: React.PropTypes.func,
        printingEnabled: React.PropTypes.bool
    },
    getDefaultProps() {
        return {
            pluginsDef: {plugins: {}, requires: {}},
            initialActions: [],
            printingEnabled: false,
            appStore: () => ({dispatch: () => {}}),
            appComponent: () => <span/>
        };
    },
    componentWillMount() {
        const onInit = () => {
            if (!global.Intl ) {
                require.ensure(['intl', 'intl/locale-data/jsonp/en.js', 'intl/locale-data/jsonp/it.js'], (require) => {
                    global.Intl = require('intl');
                    require('intl/locale-data/jsonp/en.js');
                    require('intl/locale-data/jsonp/it.js');
                    this.init();
                });
            } else {
                this.init();
            }
        };
        const opts = assign({}, this.props.storeOpts, {
            onPersist: onInit
        });
        this.store = this.props.appStore(this.props.pluginsDef.plugins, opts);
        if (!opts.persist) {
            onInit();
        }
    },
    render() {
        const {plugins, requires} = this.props.pluginsDef;
        const {pluginsDef, appStore, initialActions, appComponent, ...other} = this.props;
        const App = this.props.appComponent;
        return (
            <Provider store={this.store}>
                <App {...other} plugins={assign(PluginsUtils.getPlugins(plugins), {requires})}/>
            </Provider>
        );
    },
    init() {
        this.store.dispatch(changeBrowserProperties(ConfigUtils.getBrowserProperties()));
        if (urlQuery.localConfig) {
            ConfigUtils.setLocalConfigurationFile(urlQuery.localConfig + '.json');
        }
        ConfigUtils.loadConfiguration().then((config) => {
            this.store.dispatch(localConfigLoaded(config));
            const locale = LocaleUtils.getUserLocale();
            this.store.dispatch(loadLocale(null, locale));
            if (this.props.printingEnabled) {
                this.store.dispatch(loadPrintCapabilities(ConfigUtils.getConfigProp('printUrl')));
            }
            this.props.initialActions.forEach((action) => {
                this.store.dispatch(action());
            });
        });
    }
});

module.exports = StandardApp;
