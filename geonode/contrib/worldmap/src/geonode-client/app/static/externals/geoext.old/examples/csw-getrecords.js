Ext.onReady(function() {

    // create store
    var store = new Ext.data.Store({
        reader: new GeoExt.data.CSWRecordsReader({
            fields: ['title', 'subject']
        }),
        url: "data/cswrecords.xml",
        autoLoad: true
    });

    // create grid to display records from the store
    var grid = new Ext.grid.GridPanel({
        title: "CSW Records",
        store: store,
        columns: [
            {id: 'title', header: "Title", dataIndex: "title", sortable: true},
            {header: "Subject", dataIndex: "subject", sortable: true, width: 300}
        ],
        autoExpandColumn: 'title',
        renderTo: "cswgrid",
        height: 300,
        width: 650
    });
});
