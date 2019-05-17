/*eslint-disable */
function init() {
/*eslint-enable */
    var cfg;
    var cfgUrl;
    var theme;
    var embeddedPlugins;
    var pluginsCfg;

    /*eslint-disable */
    cfg = MapStore2.loadConfigFromStorage('mapstore.example.plugins.' + MapStore2.getParamFromRequest('map'));
    cfgUrl = MapStore2.getParamFromRequest('config');
    theme = MapStore2.getParamFromRequest('theme');
    /*eslint-enable */
    embeddedPlugins = {
        "desktop": [
            "Map",
            "MousePosition",
            "Toolbar",
            "ZoomAll",
            "Expander",
            "ZoomIn",
            "ZoomOut",
            "ScaleBox",
            "OmniBar",
            "Search",
            "DrawerMenu",
            "TOC",
            "BackgroundSwitcher",
            "Identify"
      ]};
    /*eslint-disable */
    pluginsCfg = cfg && MapStore2.buildPluginsCfg(cfg.pluginsCfg.standard, cfg.userCfg) || embeddedPlugins;
    MapStore2.create('container', {
        plugins: pluginsCfg,
        configUrl: cfgUrl,
        initialState: cfg && cfg.state && {
            defaultState: cfg.state
        } || null,
        style: cfg && cfg.customStyle,
        theme: theme ? {
            theme: theme,
            path: '../../dist/themes'
        } : {
            path: '../../dist/themes'
        }
    });
    MapStore2.onAction('CHANGE_MAP_VIEW', function(action) {
        console.log('ZOOM: ' + action.zoom);
    });
    MapStore2.onStateChange(function(map) {
        console.log('STATE ZOOM: ' + map.zoom);
    }, function(state) {
        return (state.map && state.map.present) || state.map || {}
    });
    /*eslint-enable */
}
