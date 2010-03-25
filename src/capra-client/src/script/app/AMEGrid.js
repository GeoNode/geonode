Ext.namespace("capra");
capra.AMEGrid = Ext.extend(Ext.util.Observable, {
    gridTitleText: 'UT: AME Data',
    countryLabelText: 'UT: Country',
    scenarioLabelText: 'UT: Scenario',
    ameLabelText: 'UT: Name',
    singularFileText: 'UT:File',
    pluralFilesText: 'UT:Files',
    downloadText: 'UT:Download',
    fileDetailsText: 'UT: More Information about this file',
    
    /**
     * A store containing metadata for the AME files stored on this server.
     */
    ameStore: null, 
    
    constructor: function(config) {
        /* expects: renderTo, file_info_url */
        Ext.apply(this, config);
        this.loadData();
    }, 

    loadData: function() {
        this.ameStore = new Ext.data.GroupingStore({
            proxy: new Ext.data.HttpProxy({url: this.file_info_url}),
            reader: new Ext.data.JsonReader({fields: ['name','download_url', 'edit_url', 'filename', 'scenario','country']}),
            groupField: 'scenario',
            sortInfo: {field: 'scenario', direction: 'ASC'},
            groupOnSort: true
        });
        gxp.util.dispatch(
            [function(done) {
                this.ameStore.load({callback: done, scope: this});
             }], this.doLayout, this);
    }, 

    doLayout: function() {
        var ame_detail = '<p><b>' + this.downloadText + '</b> <a class = "download ame" href="{download_url}">{filename}</a></p>'
                       + '<p><a href="{edit_url}">' + this.fileDetailsText  + '</a>';

        var ameExpander = new Ext.grid.RowExpander({
            tpl: new Ext.Template(ame_detail)
        });

        new Ext.grid.GridPanel({
            renderTo: this.renderTo,
            title: this.gridTitleText,
            store: this.ameStore,
            plugins: [ameExpander],
            columns: [
                ameExpander,
                {header: this.ameLabelText, dataIndex: 'name' },
                {header: this.scenarioLabelText, dataIndex: 'scenario'},
                {header: this.countryLabelText, dataIndex: 'country'}
            ],
            height: 200,
            view: new Ext.grid.GroupingView({
                forceFit:true,
                // custom grouping text template to display the number of items per group
                groupTextTpl: '{text} ({[values.rs.length]} ' +
                    '{[values.rs.length == 1 ? "' + this.singularFileText + 
                    '" : "' + this.pluralFilesText +'"]})'
            }),
            viewConfig: {autoFill: true}
        });
    }
});
