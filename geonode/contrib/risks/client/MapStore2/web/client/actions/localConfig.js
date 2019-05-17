const LOCAL_CONFIG_LOADED = 'LOCAL_CONFIG_LOADED';

function localConfigLoaded(config) {
    return {
        type: LOCAL_CONFIG_LOADED,
        config
    };
}
module.exports = {LOCAL_CONFIG_LOADED, localConfigLoaded};
