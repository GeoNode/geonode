
var CommunityPage = Ext.extend(Page, {

    /**
     * Property: capabilities
     * {GeoExt.data.WMSCapabilitiesStore} A store containing a record for each
     *     layer on the server.
     */
    capabilities: null,

    /**
     * Property: capGrid
     * {<Ext.Window>} A window which includes a CapabilitiesGrid panel.
     */
    capGrid: null,

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

    constructor: function(config) {

	// pass on any proxy config to OpenLayers
	if(this.proxy) {
	    OpenLayers.ProxyHost = this.proxy;
	}

        Page.prototype.constructor.apply(this, arguments);
    },


    /**
     * Method: owsURL
     */

    owsURL : function(params){
        var argIndex = this.ows.indexOf("?");
        if(argIndex > -1) {
            var search = this.ows.substring(this.ows.indexOf("?")+1);
            var url = this.ows.replace(search, Ext.urlEncode(Ext.apply(
                Ext.urlDecode(search), params)));
        } else {
            url = this.ows + "?" + Ext.urlEncode(params);
        }
        if(this.proxy) {
            url = this.proxy + encodeURIComponent(url);
        }

        return url;
    },



    /**
     * Method: createLayout
     * Create the various parts that compose the layout.
     */
    createLayout: function() {

	// create layer store
	this.layers = new GeoExt.data.LayerStore({});
    },

    /**
     * Method: activate
     * Activate the application.  Call after application is configured.
     */
    activate: function() {
	this.initPanel();

	// initialize tooltips
	Ext.QuickTips.init();

	this.fireEvent("ready");
    },


    /**
     * Method: owsURL
     */

    restURL : function(params){
        var argIndex = this.rest.indexOf("?");
        if(argIndex > -1) {
            var search = this.rest.substring(this.rest.indexOf("?")+1);
            var url = this.ows.replace(search, Ext.urlEncode(Ext.apply(
                Ext.urlDecode(search), params)));
        } else {
            url = this.rest + "?" + Ext.urlEncode(params);
        }

        return url;
    },

    /**
     * Method: initPanel
     * Constructs the map grid.
     */
    initPanel: function() {

        var mapGrid = new MapGrid({
            id: "map-browser",
            store : new Ext.data.JsonStore({
                url: this.restURL(),
                root: 'maps',
                id: 'id',
                fields: [
                    {name: 'id', mapping: 'id'},
                    {name: "title", mapping: "config.about.title"},
                    {name: "tags", mapping: "config.about.tags"},
                    {name: "abstract", mapping: "config.about.abstract"},
                    {name: "contact", mapping: "config.about.contact"},
                    {name: "featured", mapping: "config.about.featured"}
                ],
                autoLoad: true,
                listeners : {
                    "load" : function(store){
                        store.filterBy(function(record){
                            return !record.get("featured");
                        });
                    }
                }
            })
        });
    }
});
