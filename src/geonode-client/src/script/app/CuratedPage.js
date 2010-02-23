
var CuratedPage = Ext.extend(MapBrowser, {
    page: {
        'map-description': 'UT:' ,
        sidebar: '<h2> UT: CAPRA Maps</h2>' +
            '<p> CAPRA Maps are special maps chosen by CAPRA.</p>'
    },

    filterStore: function(store) {
        store.filter("endorsed", true);
    }
});
