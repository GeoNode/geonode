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

StreetViewPopup = OpenLayers.Class(OpenLayers.Control, {

    popup: null,
    mapPanel: null,
    titleHeader: 'Street View',
    popupHeight: 300,
    popupWidth: 300,

   defaults: {
       pixelTolerance: 1,
       stopSingle: true
   },

   initialize: function(options) {
       this.handlerOptions = OpenLayers.Util.extend(
           {}, this.defaults
       );
       OpenLayers.Control.prototype.initialize.apply(this, arguments);
       this.handler = new OpenLayers.Handler.Click(
           this, {click: this.trigger}, this.handlerOptions
       );
   },

   trigger: function(event) {
           this.openPopup(this.map.getLonLatFromViewPortPx(event.xy));
   },


    openPopup: function(location) {
           if (!location) {
               location = this.mapPanel.map.getCenter();
           }
           if (this.popup && this.popup.anc) {
               this.popup.close();
           }

           this.popup = new GeoExt.Popup({
               title: this.titleHeader,
               location: location,
               width: this.popupWidth,
               height: this.popupHeight,
               collapsible: true,
               map: this.mapPanel,
               items: [new gxp.GoogleStreetViewPanel()]
           });
           this.popup.show();
       }

});


/** api: constructor
 *  .. class:: StreetViewTool(config)
 *
 *    This plugin provides an interface to display
 *    Google Street Views
 */
gxp.plugins.StreetViewTool = Ext.extend(gxp.plugins.Tool, {

	/** api: ptype = gxp_streetviewtool */
	ptype: "gxp_streetviewtool",
	
	toolText: "Street View",

	streetViewTitle: "Google Street View",
	
	infoActionTip: "Click on the map to see Google Street View",
	
	popupHeight: 300,
	
	popupWidth: 600,
	
    /** api: method[addActions]
     */
    addActions: function() {

        var tool = this;
        var svt = new StreetViewPopup({
        	mapPanel: this.target.mapPanel, 
        	titleHeader: this.streetViewTitle, 
        	popupHeight: this.popupHeight, 
        	popupWidth: this.popupWidth});
        
        this.target.mapPanel.map.addControl(svt);
        var actions = gxp.plugins.StreetViewTool.superclass.addActions.call(this, [
            {
                tooltip: this.infoActionTip,
                iconCls: this.iconCls,
                text: this.toolText,
                id: this.id,
                pressed: false,
                toggleGroup: this.toggleGroup,
                enableToggle: true,
                allowDepress: true,
                toggleHandler: function(button, pressed) {
                        if (pressed) {
                            svt.activate();
                        } else {
                            svt.deactivate();
                        }
                }
            }
        ]);	
    }
});


Ext.preg(gxp.plugins.StreetViewTool.prototype.ptype, gxp.plugins.StreetViewTool);