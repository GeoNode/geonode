/**
 * Created with PyCharm.
 * User: mbertrand
 * Date: 4/30/12
 * Time: 9:52 AM
 * To change this template use File | Settings | File Templates.
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp");
/** api: constructor
 *  .. class:: GazetteerTool(config)
 *
 *    This plugin provides an interface to search the gazetteer
 *    (and 3rd party databases) for placenames.
 */
gxp.plugins.GazetteerTool = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gxp_gazetteertool */
    ptype: "gxp_gazetteertool",

    /** api: config[outputTarget]
     *  ``String`` Windows created by this tool are added to the map by default.
     */
    outputTarget: "map",

    /** api: config[infoActionTip]
     *  ``String`` Tip on how to use this plugin
     */
    infoActionTip: 'Enter a place name to search for',

    /** api: config[iconCls]
     *  ``String`` Icon class to use if any
     */
    iconCls: null,

    /** api: config[toolText]
     *  ``String`` Text to use for tool button
     */
    toolText: 'Gazetteer',

    /** api: config[popup]
     *  ``String`` popup for displaying placename info
     */
    popup: null,

    /** api: config[markers]
     *  ``String`` Markers layer to hold placename point
     */
    markers: new OpenLayers.Layer.Markers("Gazetteer Results",{displayInLayerSwitcher:false}),

    /** api: config[services]
     *  ``String`` Default gazetteer services to search
     */
    services: 'worldmap,google',

    /** api: config[searchingText]
     *  ``String`` Text to show when search is taking place
     */
    searchingText: 'Searching...',

    firstLoad: true,

    /** api: method[addActions]
     *  Creates the gazetteer interface, functionality, etc.
     */
    addActions: function() {

        // Text field to enter search term in
        this.searchTB = new Ext.form.TextField({
            id:'search-tb',
            width:150,
            emptyText:'Place name:',
            handleMouseEvents: true,
            enableKeyEvents: true,
            listeners: {
                render: function(el) {
                    el.getEl().on('keypress', function(e) {
                            var charpress = e.keyCode;
                            if (charpress == 13) {
                                this.performSearch();
                            }
                        }
                    );
                }
            },
            scope: this
        });

        // Button to initiate search
        this.searchBtn = new Ext.Button({
            text:'<span class="x-btn-text">Search</span>',
            handler: function() {
                this.performSearch();
            },
            scope: this
        });

        var tool = this;
        var serviceCheck = function (item, e) {
            switch (item.checked) {
                case true:
                    tool.services += ',' + item.id;
                    break;
                default:
                    tool.services = tool.services.replace(',' + item.id, '');
            }
        };

        // Gazetteer/Geocoder service options
        var geocoderWorldMap = {text: 'WorldMap', id: 'worldmap', checked: true, disabled: true, hideOnClick: false, checkHandler: serviceCheck};
        var geocoderGoogle = {text: 'Google', id: 'google', checked: true, hideOnClick: false, checkHandler: serviceCheck};
        var geocoderYahoo = {text: 'Yahoo', id: 'yahoo', checked: false, hideOnClick: false, checkHandler: serviceCheck};
        var geocoderGeonames = {text: 'GeoNames', id: 'geonames', checked: false, hideOnClick: false, checkHandler: serviceCheck};

        //Optional start date filter
        this.startDateField = new Ext.form.TextField({
            emptyText: 'From: YYYY-MM-DD'
        });

        //Optional end date filter
        this.endDateField = new Ext.form.TextField({
            emptyText: 'To: YYYY-MM-DD'
        });

        //menu for date filters
        this.dateOptions = {
            text: "Dates",
            menu: {
                xtype: 'menu',
                hideOnClick: false,
                items: [
                    this.startDateField,
                    this.endDateField
                    ]
            }
        };

        //menu for service options
        this.geocoderOptions = {
            text: "Geocoders",
            menu: {
                xtype: 'menu',
                hideOnClick: false,
                items: [
                    geocoderWorldMap,
                    geocoderGoogle,
                    geocoderYahoo,
                    geocoderGeonames
                ]
            }
        };

        //menu for filter options
        this.advancedOptions = new Ext.Button({
            text:"Advanced",
            menu: {
                items: [
                    this.geocoderOptions,
                    this.dateOptions
                ]
            }

        });


        // data store reader
        this.gazetteerReader = new Ext.data.JsonReader({
            },[
            {name: 'placename'},
            {name: 'coordinates'},
            {name: 'source'},
            {name: 'start_date'},
            {name: 'end_date'},
            {name: 'gazetteer_id'}
            ]
        );

        // data store proxy
        this.gazetteerProxy = new Ext.data.HttpProxy({
            url: '/gazetteer/'
        });

        // data store
        this.gazetteerDataStore = new Ext.data.Store({
            proxy: this.gazetteerProxy,
            reader:this.gazetteerReader
        });

        this.searchMask = new Ext.LoadMask(Ext.getBody(), {
            msg: this.searchingText,
            store: this.gazetteerDataStore
        });


        var markers = this.markers;
        var map = this.target.mapPanel.map;



        var onPopupClose = function (evt) {
            // 'this' is the popup.
            this.destroy();
        };

        /*
         * generate popup for placename marker
         */
        var showPopup = function (record) {
            var latlon = record.get('coordinates');
            var lonlat = new OpenLayers.LonLat(latlon[1],latlon[0]).transform("EPSG:4326", map.projection);
            var startDate = record.get("start_date") || "N/A";
            var endDate = record.get("end_date") || "N/A";

            this.popup = new OpenLayers.Popup.FramedCloud("featurePopup",
                lonlat,
                new OpenLayers.Size(100,100),
                "<h2>"+ record.get("placename") + "</h2>" +
                    "Source: " + record.get("source") + '<br/>' +
                    (startDate != "N/A" ?
                        "Start Date: " + startDate + "<br/>" : "") +
                    (endDate != "N/A" ?
                        "End Date: " + endDate + "<br/>" : ""),
                null, true, onPopupClose);
            map.addPopup(this.popup, true);
        };


        // Function to create a marker for selected placename in results grid
        var createMarker = function(grid, rowIndex) {
            var record = grid.getStore().getAt(rowIndex);
            var latlon = record.get('coordinates');
            var lonlat = new OpenLayers.LonLat(latlon[1],latlon[0]).transform("EPSG:4326", map.projection);
            markers.clearMarkers();
            var marker = new OpenLayers.Marker(lonlat);
            marker.events.register('mousedown', marker, function(evt) { showPopup(record); OpenLayers.Event.stop(evt); });
            markers.addMarker(marker);
            showPopup(record);
            return lonlat;
        };

        // Create the marker for clicked placename in results grid
        var handleRowClick = function(grid, rowIndex,columnIndex, e) {
            createMarker(grid, rowIndex);
        };

        // Create marker and center in map if placename double-clicked
        var handleDblClick =  function(grid, rowIndex,columnIndex, e) {
            var newCenter = createMarker(grid, rowIndex);
            map.setCenter(newCenter);
        };

        // Grid to display search results
        this.gazetteerGrid = new Ext.grid.GridPanel({
            store:this.gazetteerDataStore,
            width: 700,
            columns: [
                {header: 'Place Name', width:200, dataIndex: 'placename', sortable: true},
                {header: 'Coordinates', width:100, dataIndex: 'coordinates', sortable: false,
                    renderer: function(value) {
                        // your logic here
                        return value[0].toFixed(2) + ', ' + value[1].toFixed(2);
                    }
                },
                {header: 'Source', width:200, dataIndex: 'source', sortable: true},
                {header: 'Start Date', width:100, dataIndex: 'start_date', sortable: true},
                {header: 'End Date', width:100, dataIndex: 'end_date', sortable: true}
                //{header: 'ID', width:100, dataIndex: 'gazetteer_id', sortable: true}
            ],
            listeners:
            {
                'rowclick': handleRowClick,
                'rowdblclick': handleDblClick
            }
        });



        //Toolbar for gazetteer
        this.gazetteerToolbar  = new Ext.Toolbar({
            items:[
                this.searchTB,
                this.searchBtn,
                this.advancedOptions
            ]
        });

        //Panel for gazetteer
        this.gazetteerPanel = new Ext.Panel({
            height:300,
            width:700,
            layout: 'fit',
            items: [
                this.gazetteerGrid
            ],
            tbar: this.gazetteerToolbar
        });

        //Gazetteer search window
        var gazetteerWindow = new Ext.Window({
            title: this.title,
            layout: "fit",
            width: 700,
            autoHeight: true,
            closeAction: "hide",
            listeners:{
                hide: function(){
                    map.removeLayer(markers);
                }
            },
            items: [ this.gazetteerPanel ]
        });


        var actions = gxp.plugins.GazetteerTool.superclass.addActions.call(this, [
            {
                tooltip: this.infoActionTip,
                iconCls: this.iconCls,
                id: this.id,
                text: this.toolText,
                handler: function() {
                        gazetteerWindow.show();
                        map.addLayer(markers);

                }
            }
        ]);


        return actions;
    },


    //Query gazetteer & geocoders for placenames
    performSearch: function() {

    this.gazetteerDataStore.proxy.conn.url = '/gazetteer/' + this.searchTB.getValue() + '/Service/' + this.services
        + (this.startDateField.getValue() && this.startDateField.getValue() !== '' ? '/StartDate/' + this.startDateField.getValue(): '')
        + (this.endDateField.getValue() && this.endDateField.getValue() !== '' ? '/EndDate/' + this.endDateField.getValue(): '');

    if (this.firstLoad === true)
    {
        this.gazetteerDataStore.load();
        this.firstLoad = false;
    }
    else
        this.gazetteerDataStore.reload();
    }

});

Ext.preg(gxp.plugins.GazetteerTool.prototype.ptype, gxp.plugins.GazetteerTool);