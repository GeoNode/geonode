var MapGrid = Ext.extend(Ext.grid.GridPanel, {


    //rest URL for getting the maps
    url: null,

    autoScroll: true,
    autoExpandColumn: 'title',
    renderTo: "map-browser",
    height: 300,

    createMapText : "UT:Create Map",
    exportMapText: "UT: Export Map",
    mapAbstractLabelText: "UT:Abstract",
    mapContactLabelText: "UT:Contact",
    mapGridText : "UT:Map",
    mapLinkLabelText: "UT:View this Map",
    mapTitleLabelText: "UT:Title",
    openMapText : "UT:Open Map",

    initComponent: function(){

        this.store = this.store || new Ext.data.JsonStore({
            url: this.url,
            root: 'maps',
            id: 'id',
            fields: [
                {name: 'id', mapping: 'id'},
                {name: "title", mapping: "config.about.title"},
                {name: "abstract", mapping: "config.about.abstract"},
                {name: "contact", mapping: "config.about.contact"}
            ],
            autoLoad: true
        });

        if(!this.expander){

            var tpl = new Ext.Template('<p><b>' + this.mapAbstractLabelText + ':</b> {abstract}</p>'+
                                       '<p><a href="/maps/{id}">' + this.mapLinkLabelText + '</a></p>');

            this.expander = new Ext.grid.RowExpander({tpl: tpl});
        }

        if(!this.plugins){
            this.plugins = this.expander;
        }

        if(!this.cm){
            this.cm = new Ext.grid.ColumnModel([
                this.expander,
                {id: 'title', header: this.mapTitleLabelText, dataIndex: 'title', sortable: true, 
				renderer: function(value,metaData,record) { 
					return "<a href='/maps/" + record.get('id') +  "'>" + value + "</a>" ; } 
				
				},
                {id: 'contact', header: this.mapContactLabelText, dataIndex: 'contact', width: 250, sortable: true}
            ]);
        }

        var mapGrid = this;

        this.listeners = Ext.applyIf(this.listeners || {}, {
            "rowdblclick": function(grid, rowIndex, evt) {
                var rec = grid.store.getAt(rowIndex);
                if (rec != null) {
                    location.href = "/maps/" + rec.id;
                }
            }
        });

        MapGrid.superclass.initComponent.call(this);
    },

    showExportWizard: function(mapid) {
        new ExportWizard(mapid).show();
    }
});

