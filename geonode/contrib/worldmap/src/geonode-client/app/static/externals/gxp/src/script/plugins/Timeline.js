/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @requires widgets/TimelinePanel.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = Timeline
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: Timeline(config)
 *
 *    Provides an action to display a legend in a new window.
 */
gxp.plugins.Timeline = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_timeline */
    ptype: "gxp_timeline",

    /** api: config[playbackTool]
     *  ``String``
     *  Id of the playback tool to which the timeline has to bind.
     */
    playbackTool: null,

    /** api: config[featureEditor]
     *  ``String``
     *  Id of the feature editor tool to which the timeline has to bind.
     */
    featureEditor: null,
    
    /** api: config[menuText]
     *  ``String``
     *  Text for legend menu item (i18n).
     */
    menuText: "Timeline",

    /** api: config[tooltip]
     *  ``String``
     *  Text for legend action tooltip (i18n).
     */
    tooltip: "Show Timeline",

    /** api: config[actionTarget]
     *  ``Object`` or ``String`` or ``Array`` Where to place the tool's actions
     *  (e.g. buttons or menus)? Use null as the default since our tool has both 
     *  output and action(s).
     */
    actionTarget: null,
    
    /** private: method[constructor]
     */
    constructor: function(config) {
        gxp.plugins.Timeline.superclass.constructor.apply(this, arguments);
        
        if (!this.outputConfig) {
            this.outputConfig = {};
        }
        Ext.applyIf(this.outputConfig, {title: this.menuText});
    },

    /** api: method[addActions]
     */
    addActions: function() {
        var actions = [{
            menuText: this.menuText,
            tooltip: this.tooltip,
            handler: function() {
                this.addOutput();
            },
            scope: this
        }];
        return gxp.plugins.Timeline.superclass.addActions.apply(this, [actions]);
    },

    /** private: method[addOutput]
     *  :arg config: ``Object``
     */
    addOutput: function(config) {
        return gxp.plugins.Timeline.superclass.addOutput.call(this, Ext.apply({
            xtype: "gxp_timelinepanel",
            viewer: this.target,
            featureEditor: this.target.tools[this.featureEditor],
            playbackTool: this.target.tools[this.playbackTool]
        }, this.outputConfig));
    },

    /** api: method[getTimelinePanel]
     *  :returns: ``gxp.TimelinePanel``
     *
     *  Get the timeline panel associated with this timeline plugin.
     */
    getTimelinePanel: function() {
        return this.output[0];
    },

    /** api: method[getState]
     *  :returns {Object} - initial config plus any user configured settings
     *  
     *  Tool specific implementation of the getState function
     */
    getState: function() {
        var config = gxp.plugins.Timeline.superclass.getState.call(this);
        config.outputConfig = Ext.apply(config.outputConfig || {}, this.getTimelinePanel().getState());
        return config;
    }
});

Ext.preg(gxp.plugins.Timeline.prototype.ptype, gxp.plugins.Timeline);
