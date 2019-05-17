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

    const {Provider} = require('react-redux');

    // initializes Redux store
    var store = require('./stores/featuregridstore');

    const {loadMapConfig} = require('../../actions/config');
    const {changeBrowserProperties} = require('../../actions/browser');
    const {loadLocale} = require('../../actions/locale');

    const ConfigUtils = require('../../utils/ConfigUtils');
    const LocaleUtils = require('../../utils/LocaleUtils');
    const url = require('url');

    // reads parameter(s) from the url
    const urlQuery = url.parse(window.location.href, true).query;

    // get configuration file url (defaults to config.json on the app folder)
    const { configUrl, legacy } = ConfigUtils.getConfigurationOptions(urlQuery, 'config', 'json');

    // dispatch an action to load the configuration from the config.json file
    store.dispatch(loadMapConfig(configUrl, legacy));

    store.dispatch(changeBrowserProperties(ConfigUtils.getBrowserProperties()));

    const FeatureGrid = require('./containers/FeatureGrid');

    // we spread the store to the all application
    // wrapping it with a Provider component
    const FeatureGridApp = React.createClass({
        render() {
            return (
            <Provider store={store}>
                <FeatureGrid/>
            </Provider>);
        }
    });

    let locale = LocaleUtils.getUserLocale();
    store.dispatch(loadLocale('../../translations', locale));
    // Renders the application, wrapped by the Redux Provider to connect the store to components
    ReactDOM.render(<FeatureGridApp/>, document.getElementById('container'));
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
