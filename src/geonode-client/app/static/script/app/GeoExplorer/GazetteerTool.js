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
 *  .. class:: GeoNodeQueryTool(config)
 *
 *    This plugins provides an action which, when active, will issue a
 *    GetFeatureInfo request to the WMS of all layers on the map. The output
 *    will be displayed in a popup.
 */
gxp.plugins.GazetteerTool = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = geo_getfeatureinfo */
    ptype: "gxp_gazetteertool",

    /** api: config[outputTarget]
     *  ``String`` Popups created by this tool are added to the map by default.
     */
    outputTarget: "map",

    gazetteerPanel: 'gridResultsPanel',

    infoActionTip: 'Tip',

    iconCls: null,

    toolText: 'Gazetteer',


    mapid: null,

    markers: new OpenLayers.Layer.Markers("Gazetteer Results",{displayInLayerSwitcher:false}),

    /** api: config[vendorParams]
     *  ``Object``
     *  Optional object with properties to be serialized as vendor specific
     *  parameters in the requests (e.g. {buffer: 10}).
     */

    /** api: config[paramsFromLayer]
     *  ``Array`` List of param names that should be taken from the layer and
     *  added to the GetFeatureInfo request (e.g. ["CQL_FILTER"]).
     */

    /** api: method[addActions]
     */
    addActions: function() {

        var tool = this;


        var searchTB = new Ext.form.TextField({
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
                                performSearch();
                            }
                        }
                    );
                }
            }
        });


        var psHandler = function() {
            performSearch();
        };

        var searchBtn = new Ext.Button({
            text:'<span class="x-btn-text">Search</span>',
            handler: psHandler
        });

        var services = 'worldmap,google';

        var serviceCheck = function(item, e) {
           switch (item.checked)
           {
               case true:
                   services += ',' + item.id;
                   break;
               default:
                  services = services.replace(',' + item.id,'')
           }
        };

        var geocoderWorldMap = {text: 'WorldMap', id: 'worldmap', checked: true, disabled: true, hideOnClick: false, checkHandler: serviceCheck};
        var geocoderGoogle = {text: 'Google', id: 'google', checked: true, hideOnClick: false, checkHandler: serviceCheck};
        var geocoderYahoo = {text: 'Yahoo', id: 'yahoo', checked: false, hideOnClick: false, checkHandler: serviceCheck};
        var geocoderGeonames = {text: 'GeoNames', id: 'geonames', checked: false, hideOnClick: false, checkHandler: serviceCheck};


        var startDateField = new Ext.form.TextField({
            emptyText: 'From: YYYY-MM-DD'
        })

        var endDateField = new Ext.form.TextField({
            emptyText: 'To: YYYY-MM-DD'
        })

        var dateOptions = {
            text: "Dates",
            menu: {
                xtype: 'menu',
                hideOnClick: false,
                items: [
                    startDateField,
                    endDateField
                    ]
            }
        };

        var geocoderOptions = {
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

        var advancedOptions = new Ext.Button({
            text:"Advanced",
            menu: {
                items: [
                    geocoderOptions,
                    dateOptions
                ]
            }

        });



        var gazetteerReader = new Ext.data.JsonReader({
            },[
            {name: 'placename'},
            {name: 'coordinates'},
            {name: 'source'},
            {name: 'start_date'},
            {name: 'end_date'},
            {name: 'gazetteer_id'}
        ]
        );


        var gazetteerProxy = new Ext.data.HttpProxy({
            url: '/gazetteer/'
        });

        var gazetteerDataStore = new Ext.data.Store({
            proxy: gazetteerProxy,
            reader:gazetteerReader
        });

        var firstLoad = true;

        var performSearch = function() {

            gazetteerDataStore.proxy.conn.url = '/gazetteer/' + searchTB.getValue() + '/Service/' + services
                + (startDateField.getValue() && startDateField.getValue() !== '' ? '/StartDate/' + startDateField.getValue(): '')
                + (endDateField.getValue() && endDateField.getValue() !== '' ? '/EndDate/' + endDateField.getValue(): '');

            if (firstLoad === true)
            {
                gazetteerDataStore.load();
                firstLoad = false;
            }
            else
                gazetteerDataStore.reload();



        }


        var createMarker = function(grid, rowIndex) {
            var record = grid.getStore().getAt(rowIndex);
            var latlon = record.get('coordinates');
            var lonlat = new OpenLayers.LonLat(latlon[1],latlon[0]).transform("EPSG:4326", tool.target.mapPanel.map.projection);
            tool.markers.clearMarkers();
            var marker = new OpenLayers.Marker(lonlat);
            marker.events.register('mousedown', marker, function(evt) { alert(record['placename']); OpenLayers.Event.stop(evt); });
            tool.markers.addMarker(marker);
            return lonlat;
        };

        var handleRowClick = function(grid, rowIndex,columnIndex, e) {
            createMarker(grid, rowIndex);
        };

        var handleDblClick =  function(grid, rowIndex,columnIndex, e) {
            var newCenter = createMarker(grid, rowIndex);
            tool.target.mapPanel.map.setCenter(newCenter);
        };

        var gazetteerGrid = new Ext.grid.GridPanel({
            store:gazetteerDataStore,
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




        var gazetteerToolbar  = new Ext.Toolbar({
            items:[
                searchTB,
                searchBtn,
                advancedOptions
            ]
        });

        var gazetteerPanel = new Ext.Panel({
            height:300,
            width:700,
            layout: 'fit',
            items: [
                gazetteerGrid
            ],
            tbar: gazetteerToolbar
        });

        var gazetteerWindow = new Ext.Window({
            title: this.title,
            layout: "fit",
            width: 700,
            autoHeight: true,
            closeAction: "hide",
            listeners:{
                hide: function(){
                    tool.target.mapPanel.map.removeLayer(tool.markers);
                }
            },
            items: [ gazetteerPanel ]
        });




        var actions = gxp.plugins.CoordinateTool.superclass.addActions.call(this, [
            {
                tooltip: this.infoActionTip,
                iconCls: this.iconCls,
                id: this.id,
                text: this.toolText,
                handler: function() {
                        gazetteerWindow.show();
                        tool.target.mapPanel.map.addLayer(tool.markers);

                }
            }
        ]);

        return actions;
    }

});

Ext.preg(gxp.plugins.GazetteerTool.prototype.ptype, gxp.plugins.GazetteerTool);