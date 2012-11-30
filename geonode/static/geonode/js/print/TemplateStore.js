Ext.namespace("GeoExplorer");

GeoExplorer.TemplateStore = Ext.extend(Ext.data.JsonStore, {
    storeId: 'printTemplates',
    constructor: function(config) {
        this.initialConfig = config;
        var defConfig = {
            idProperty: 'id',
            fields: ['id', 'title', 'contents', 'url'],
            root: null
        };
        if(config.fields) {
            config.fields = defConfig.fields.concat(config.fields);
        }
        Ext.applyIf(config, defConfig);
        Ext.apply(this, config);
        GeoExplorer.TemplateStore.superclass.constructor.apply(this, arguments);
    }
});
