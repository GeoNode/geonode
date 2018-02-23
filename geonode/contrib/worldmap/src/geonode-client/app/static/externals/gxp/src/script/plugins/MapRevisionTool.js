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
gxp.plugins.MapRevisionTool = Ext.extend(gxp.plugins.Tool, {

	/** api: ptype = gxp_gazetteertool */
	ptype: "gxp_maprevisiontool",

	/** api: config[outputTarget]
	 *  ``String`` Windows created by this tool are added to the map by default.
	 */
	outputTarget: "map",

	/** api: config[infoActionTip]
	 *  ``String`` Tip on how to use this plugin
	 */
	infoActionTip: 'View a list of map revisions',

	/** api: config[iconCls]
	 *  ``String`` Icon class to use if any
	 */
	iconCls: null,

	/** api: config[toolText]
	 *  ``String`` Text to use for tool button
	 */
	toolText: 'Revisions',
	
	windowTitle: "Map Revision History",
	
	hidden: false,
	
	disabled: false,

	addActions: function() {

		var store = new Ext.data.JsonStore({
			url: '/maps/history/' + this.target.id,
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
			title: this.windowTitle,
			closeAction: 'hide',
			items: grid,
			modal: true,
			autoScroll: true
		});


		var actions = gxp.plugins.MapRevisionTool.superclass.addActions.call(this, 
				[
				 {
					 tooltip: this.infoActionTip,
					 iconCls: this.iconCls,
					 id: this.id,
					 text: this.toolText,
					 hidden: this.hidden,
					 disabled: this.disabled,
					 handler: function() {
						 store.load();
						 historyWindow.show();
					 }
				 }
				 ]);


		return actions;    	    
	}


});

Ext.preg(gxp.plugins.MapRevisionTool.prototype.ptype, gxp.plugins.MapRevisionTool);