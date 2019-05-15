var React = require('react');
var ReactDOM = require('react-dom');

var Provider = require('react-redux').Provider;

// include application component
var MyApp = require('./containers/myapp');
var url = require('url');

var loadMapConfig = require('../../actions/config').loadMapConfig;
var ConfigUtils = require('../../utils/ConfigUtils');

// initializes Redux store
var store = require('./stores/myappstore');

// reads parameter(s) from the url
const urlQuery = url.parse(window.location.href, true).query;

// get configuration file url (defaults to config.json on the app folder)
const { configUrl, legacy } = ConfigUtils.getConfigurationOptions(urlQuery, 'config', 'json');

// dispatch an action to load the configuration from the config.json file
store.dispatch(loadMapConfig(configUrl, legacy));

// Renders the application, wrapped by the Redux Provider to connect the store to components
ReactDOM.render(
    <Provider store={store}>
        <MyApp />
    </Provider>,
    document.getElementById('container')
);
