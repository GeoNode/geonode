
Ext.namespace("GeoExplorer");

/** api: constructor
 *  A tool to display all previously saved versions of a map, along with date and user.
 */
GeoExplorer.MapSnapshotGrid =  function(mapid) {


var store = new Ext.data.JsonStore({
    url: '/maps/history/' + mapid,
    fields: [{name:'created', type: 'date'}, 'user', 'url', 'map'],
    idProperty: 'url',
    root: '',
    sortInfo: {
        field: 'created',
        direction: 'DESC' // or 'DESC' (case sensitive for local sorting)
    }
});

    var renderDate = function(value, p, record){
        return String.format(
                '<b><a href="/maps/{0}/{1}">{2}</a>',
                record.data.map, record.id, value);
    };

    var renderUser = function(value, p, record){
        return String.format(
                '<b><a href="/profiles/{0}">{1}</a>',
                value, value);
    };

    
var grid = new Ext.grid.GridPanel({
        width:400,
        height:300,
        store: store,
        trackMouseOver:false,

        // grid columns
        columns:[{
            header: "Revision Date",
            dataIndex: 'created',
            width: 200,
            renderer: renderDate,
            sortable: true
        },{
            header: "URL",
            dataIndex: 'url',
            width: 10,
            hidden: true,
            sortable: false
        },{
            header: "User",
            dataIndex: 'user',
            width: 200,
            align: 'right',
            renderer: renderUser,
            sortable: true
        },{
            header: "Map",
            dataIndex: 'map',
            width: 10,
            align: 'right',
            hidden:true,
            sortable: false
        }],

        // customize view config
        viewConfig: {
            forceFit:true
        }
    });




    var historyWindow = new Ext.Window({
            title: 'Map Revision History',
            closeAction: 'destroy',
            items: grid,
            modal: true,
            autoScroll: true
        });


    // trigger the data store load
    store.load();

    historyWindow.show();

}