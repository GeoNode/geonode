
var FeaturedPage = Ext.extend(Page, {

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
        'map-description': 'UT:' ,
        sidebar: '<h2> UT: CAPRA Maps</h2>' +
            '<p> CAPRA Maps are special maps chosen by CAPRA.</p>'
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
	this.populateContent();

	// create layer store
	//TODO
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
                        store.filter("featured", true);
                    }
                }
            })
        });
    }
});
