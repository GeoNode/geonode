var CommunityPage = Ext.extend(MapBrowser, {
    page: {
        'map-description': '',
        sidebar: '<h3> UT: Contributed Maps</h3>' +
            '<p> Contributed Maps are made by people like you.  ' +
            'They are made from data hosted by the CAPRA GeoNode, ' +
            'as well as data hosted by other entities.</p>' +
            '<p> You can browse the contributed maps using the grid to the right.' +
            'Select one and click <strong>Open Map</strong> to open it in a map editor, ' +
            'or click <strong>Export Map</strong> to export it as a widget.</p>' +
            '<p>Or click here to <a href="map.html">create your own map</a>!</p>'
    },

    filterStore: function(store) {
        store.filter("endorsed", false);
    }
});
