/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const startApp = () => {
    var React = require('react');
    var ReactDOM = require('react-dom');

    var Provider = require('react-redux').Provider;

    // include application component
    var Viewer = require('./containers/Viewer');

    var {loadMapConfig} = require('../../actions/config');
    var {loadLocale} = require('../../actions/locale');

    var ConfigUtils = require('../../utils/ConfigUtils');
    const LocaleUtils = require('../../utils/LocaleUtils');

    // initializes Redux store
    var store = require('./stores/store');

    ConfigUtils.loadConfiguration().then(() => {
        const { configUrl, legacy } = ConfigUtils.getUserConfiguration('config', 'json');
        store.dispatch(loadMapConfig(configUrl, legacy));

        let locale = LocaleUtils.getUserLocale();
        store.dispatch(loadLocale('../../translations', locale));
    });

    // Renders the application, wrapped by the Redux Provider to connect the store to components
    ReactDOM.render(
        <Provider store={store}>
            <Viewer />
        </Provider>,
        document.getElementById('container')
    );
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
