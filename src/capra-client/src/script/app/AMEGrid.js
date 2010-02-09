Ext.namespace("capra");
capra.AMEGrid = Ext.extend(Ext.util.Observable, {
    countryLabelText: 'UT: Country',
    scenarioLabelText: 'UT: Scenario',
    ame_link_prefix: 'http://localhost:8001/geoserver/www',
    ameLabelText: 'UT:AME File',
    singularFile: 'UT:File',
    pluralFiles: 'UT:Files',

    /**
     * A store containing metadata for the AME files stored on this server.
     */
    ameStore: null, 
    
    constructor: function(config) {
        Ext.apply(this, config);
        this.loadData();
    }, 

    loadData: function() {
        var json_url = this.ows.replace(/\/...$/, '') + "/www/out.json";
        if (this.proxy) {
            json_url = this.proxy + "?" + Ext.urlEncode({ "url": json_url });
        }

        this.ameStore = new Ext.data.GroupingStore({
            proxy: new Ext.data.HttpProxy({url: json_url}),
            reader: new Ext.data.JsonReader({
                fields: ['rel_tifs', 'path', 'scenario', 'country']
            }),
            groupField: 'scenario',
            sortInfo: {field: 'scenario', direction: 'ASC'},
            groupOnSort: true
        });

        gxp.util.dispatch([
                function(done) {
                    this.ameStore.load({
                        callback: done,
                        scope: this
                    });
                }
            ], 
            this.doLayout,
            this
        );
    }, 

    doLayout: function() {
        var ame_link_prefix = this.ame_link_prefix;
        new Ext.grid.GridPanel({
            title: 'AME Data',
            height: 200,
            store: this.ameStore,
            columns: [{
                id: 'path', 
                header: this.ameLabelText, 
                dataIndex: 'path', 
                renderer: function (path) {
                    return '<a href="' + ame_link_prefix + '/' + path + '">' + path.replace(/.*\//, '') + '</a';
                }
            }, { 
                header: this.scenarioLabelText,
                dataIndex: 'scenario' 
            }, { 
                header: this.countryLabelText, 
                dataIndex: 'country' 
            }],
            view: new Ext.grid.GroupingView({
                forceFit:true,
                // custom grouping text template to display the number of items per group
                groupTextTpl: '{text} ({[values.rs.length]} ' +
                    '{[values.rs.length == 1 ? "' + this.singularFile + 
                    '" : "' + this.pluralFiles +'"]})'
            }),
            viewConfig: {autoFill: true},
            renderTo: this.renderTo
        });
    }
});
