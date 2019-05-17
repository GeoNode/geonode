/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const React = require('react');
const ReactDOM = require('react-dom');

const {Provider} = require('react-redux');

const {changeBrowserProperties} = require('../../actions/browser');
const {loadLocale} = require('../../actions/locale');

const ConfigUtils = require('../../utils/ConfigUtils');
const LocaleUtils = require('../../utils/LocaleUtils');
const PluginsUtils = require('../../utils/PluginsUtils');


const assign = require('object-assign');

function startApp() {
    const {plugins, requires} = require('./plugins.js');
    const store = require('./stores/store')(plugins);
    const App = require('./containers/App');

    store.dispatch(changeBrowserProperties(ConfigUtils.getBrowserProperties()));

    ConfigUtils.loadConfiguration().then(() => {
        let locale = LocaleUtils.getUserLocale();
        store.dispatch(loadLocale('../../translations', locale));


    });

    ReactDOM.render(
        <Provider store={store}>
            <App plugins={assign(PluginsUtils.getPlugins(plugins), {requires})}/>
        </Provider>,
        document.getElementById('container')
    );
}
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
