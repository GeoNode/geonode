Ext.onReady(function() {
    var metaStore = new Ext.data.Store({
        reader: new Ext.data.JsonReader({
            fields: ['store', 'name', 'identifier', 'url']
        })
    });

    insert(metaStore, '/geoserver/ows?request=GetCapabilities&service=WMS');

    var grid = new gxp.grid.CapabilitiesGrid({
        renderTo: 'showGrid',
        expander: null,
        height: 300,
        width: 500,
        plugins: [],
        store: metaStore.getAt(0).get("store"),
        metaStore: metaStore,
        allowNewSources: false
    });
});

function insert(metaStore, url) {
    var store = new GeoExt.data.WMSCapabilitiesStore({
        url: url, 
        autoLoad: true
    });

    metaStore.add(new metaStore.recordType({
        'store': store,
        'name': url,
        'identifier': url,
        'url': url
    }));
}
