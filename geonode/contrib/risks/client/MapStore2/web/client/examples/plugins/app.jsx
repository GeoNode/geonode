/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const startApp = () => {
    const React = require('react');
    const ReactDOM = require('react-dom');
    const {connect} = require('react-redux');

    const ConfigUtils = require('../../utils/ConfigUtils');
    const LocaleUtils = require('../../utils/LocaleUtils');
    const PluginsUtils = require('../../utils/PluginsUtils');
    const ThemeUtils = require('../../utils/ThemeUtils');

    const {changeBrowserProperties} = require('../../actions/browser');
    const {loadMapConfig} = require('../../actions/config');
    const {loadLocale} = require('../../actions/locale');
    const {loadPrintCapabilities} = require('../../actions/print');
    const {selectTheme} = require('../../actions/theme');

    const PluginsContainer = connect((state) => ({
        pluginsState: state && state.controls || {}
    }))(require('../../components/plugins/PluginsContainer'));

    const ThemeSwitcher = connect((state) => ({
        selectedTheme: state.theme && state.theme.selectedTheme || 'default',
        themes: require('../../themes')
    }), {
        onThemeSelected: selectTheme
    })(require('../../components/theme/ThemeSwitcher'));

    const Theme = connect((state) => ({
        theme: state.theme && state.theme.selectedTheme && state.theme.selectedTheme.id || 'default'
    }))(require('../../components/theme/Theme'));

    const {plugins} = require('./plugins');

    let userPlugin;
    const Template = require('../../components/data/template/jsx/Template');

    let pluginsCfg = {
        standard: ['Map', 'Toolbar']
    };

    let customStyle = null;
    let userCfg = {};

    const {Provider} = require('react-redux');

    const {FormControl, FormGroup} = require('react-bootstrap');

    const SaveAndLoad = require('./components/SaveAndLoad');

    const Debug = require('../../components/development/Debug');

    const assign = require('object-assign');
    const codeSample = require("raw-loader!./sample.js.raw");
    const themeSample = require("raw-loader!./sample.less.raw");

    let customReducers;

    const context = require('./context');

    const customReducer = (state={}, action) => {
        if (customReducers) {
            const newState = assign({}, state);
            Object.keys(customReducers).forEach((stateKey) => {
                assign(newState, {[stateKey]: customReducers[stateKey](state[stateKey], action)});
            });
            return newState;
        }
        return state;
    };

    const store = require('./store')(plugins, customReducer);

    const {savePluginConfig, compileError, resetError} = require('./actions/config');

    require('./assets/css/plugins.css');

    const Babel = require('babel-standalone');

    let mapType = 'leaflet';

    const Localized = connect((state) => ({
        messages: state.locale && state.locale.messages,
        locale: state.locale && state.locale.current,
        loadingError: state.locale && state.locale.localeError
    }))(require('../../components/I18N/Localized'));

    const togglePlugin = (pluginName, callback) => {
        pluginsCfg.standard = pluginsCfg.standard.indexOf(pluginName) !== -1 ?
            pluginsCfg.standard.filter((plugin) => plugin !== pluginName) :
            [...pluginsCfg.standard, pluginName];
        callback();
    };

    const configurePlugin = (pluginName, callback, cfg) => {
        try {
            userCfg[pluginName] = JSON.parse(cfg);
            store.dispatch(savePluginConfig(pluginName, userCfg[pluginName]));
        } catch(e) {
            /*eslint-disable */
            alert('Error in JSON');
            /*eslint-enable */
        }
        callback();
    };

    const applyStyle = (theme, callback) => {
        if (theme) {
            ThemeUtils.renderFromLess(theme, 'custom_theme', 'themes/default/', callback);
        } else {
            document.getElementById('custom_theme').innerText = '';
            if (callback) {
                callback();
            }
        }
    };

    const customTheme = (callback, theme) => {
        customStyle = theme;
        applyStyle(theme, callback);
    };

    const customPlugin = (callback, code) => {
        /*eslint-disable */
        const require = context;
        try {
            customReducers = eval(Babel.transform(code, { presets: ['es2015', 'react', 'stage-0'] }).code).reducers || null;

            /*eslint-enable */
            userPlugin = connect(() => ({
                template: code,
                renderContent: (comp) => {
                    /*eslint-disable */
                    return eval(comp).Plugin;
                    /*eslint-enable */
                },
                getReducers() {
                    return this.comp;
                }
            }), {
                onError: compileError
            })(Template);
            store.dispatch(resetError());
            callback();
        } catch(e) {
            store.dispatch(compileError(e.message));
        }
    };

    const PluginConfigurator = require('./components/PluginConfigurator');

    const PluginCreator = connect((state) => ({
        error: state.pluginsConfig && state.pluginsConfig.error
    }))(require('./components/PluginCreator'));

    const ThemeCreator = connect((state) => ({
        error: state.pluginsConfig && state.pluginsConfig.error
    }))(require('./components/ThemeCreator'));

    const renderPlugins = (callback) => {
        return Object.keys(plugins).map((plugin) => {
            const pluginName = plugin.substring(0, plugin.length - 6);
            return (<PluginConfigurator key={pluginName} pluginName={pluginName} pluginsCfg={pluginsCfg.standard}
                pluginImpl={plugins[plugin][plugin]}
                onToggle={togglePlugin.bind(null, pluginName, callback)}
                onApplyCfg={configurePlugin.bind(null, plugin, callback)}
                pluginConfig={userCfg[pluginName + 'Plugin'] && JSON.stringify(userCfg[pluginName + 'Plugin'], null, 2) || "{}"}
                />);
        });
    };

    const isHidden = (plugin) => plugins[plugin + 'Plugin'][plugin + 'Plugin'].Toolbar && plugins[plugin + 'Plugin'][plugin + 'Plugin'].Toolbar.hide;

    const getPluginsConfiguration = () => {
        return {
            standard: pluginsCfg.standard.map((plugin) => ({
                name: plugin,
                hide: isHidden(plugin),
                cfg: userCfg[plugin + 'Plugin'] || {}
            })).concat(userPlugin ? ['My'] : [])
        };
    };

    const changeMapType = (callback, e) => {
        mapType = e.target.options[e.target.selectedIndex].value;
        callback();
    };

    const save = (callback, name) => {
        const state = assign({}, store.getState(), {
            map: assign({}, store.getState().map, {mapStateSource: null})
        });
        localStorage.setItem('mapstore.example.plugins.' + name, JSON.stringify({
            pluginsCfg,
            userCfg,
            mapType,
            state: state,
            customStyle
        }));
        callback();
    };

    const load = (callback, name) => {
        const loaded = localStorage.getItem('mapstore.example.plugins.' + name);
        if (loaded) {
            const obj = JSON.parse(loaded);
            pluginsCfg = obj.pluginsCfg;
            userCfg = obj.userCfg;
            mapType = obj.mapType || mapType;
            customStyle = obj.customStyle || null;
            if (obj.state) {
                store.dispatch({type: 'LOADED_STATE', state: obj.state});
            }
            applyStyle(customStyle, callback);
        }
    };

    const getPlugins = () => {
        return assign({}, plugins, userPlugin ? {MyPlugin: {MyPlugin: userPlugin}} : {});
    };

    const renderPage = () => {
        ReactDOM.render(
            (
                <Provider store={store}>
                    <Localized>
                        <div style={{width: "100%", height: "100%"}}>
                            <div id="plugins-list" style={{position: "absolute", zIndex: "10000", backgroundColor: "white", width: "300px", left: 0, height: "100%", overflow: "auto"}}>
                                <h5>Configure application plugins</h5>
                                <ul>
                                  <FormGroup bsSize="small">
                                    <label>Choose a map library</label>
                                    <FormControl value={mapType} componentClass="select" onChange={changeMapType.bind(null, renderPage)}>
                                        <option value="leaflet" key="leaflet">Leaflet</option>
                                        <option value="openlayers" key="openlayer">OpenLayers</option>
                                        <option value="cesium" key="cesium">CesiumJS</option>
                                    </FormControl>
                                    <Theme path="../../dist/themes"/>
                                    <label>Choose a theme</label>
                                    <ThemeSwitcher style={{width: "275px", marginTop: "5px"}}/>
                                  </FormGroup>
                                </ul>
                                <ul>
                                  <ThemeCreator themeCode={customStyle || themeSample} onApplyTheme={customTheme.bind(null, renderPage)}/>
                                </ul>
                                <ul>
                                  <label>Save &amp; Load</label>
                                  <SaveAndLoad onSave={save.bind(null, renderPage)} onLoad={load.bind(null, renderPage)}/>
                                </ul>
                                <ul>
                                    <label>Plugins</label>
                                    <PluginCreator pluginCode={codeSample} onApplyCode={customPlugin.bind(null, renderPage)}/>
                                    {renderPlugins(renderPage)}
                                </ul>
                            </div>
                            <div style={{position: "absolute", right: 0, left: "300px", height: "100%", overflow: "hidden"}}>
                                <PluginsContainer params={{mapType}} plugins={PluginsUtils.getPlugins(getPlugins())} pluginsConfig={getPluginsConfiguration()} mode="standard"/>
                            </div>
                            <Debug/>
                        </div>
                    </Localized>
                </Provider>
            ),
            document.getElementById("container"));
    };

    ConfigUtils.loadConfiguration().then(() => {
        store.dispatch(changeBrowserProperties(ConfigUtils.getBrowserProperties()));

        const { configUrl, legacy } = ConfigUtils.getUserConfiguration('config', 'json');
        store.dispatch(loadMapConfig(configUrl, legacy));

        let locale = LocaleUtils.getUserLocale();
        store.dispatch(loadLocale('../../translations', locale));

        store.dispatch(loadPrintCapabilities(ConfigUtils.getConfigProp('printUrl')));

        renderPage();
    });
};

if (!global.Intl ) {
    require.ensure(['intl', 'intl/locale-data/jsonp/en.js', 'intl/locale-data/jsonp/it.js'], (require) => {
        global.Intl = require('intl');
        require('intl/locale-data/jsonp/en.js');
        require('intl/locale-data/jsonp/it.js');
        startApp();
    });
} else {
    startApp();
}
