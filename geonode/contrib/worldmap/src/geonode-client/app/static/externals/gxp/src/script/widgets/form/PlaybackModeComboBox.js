/**
 * Copyright (c) 2008-2012 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp.form
 *  class = PlaybackModeComboBox
 *  base_link = `Ext.form.ComboBox <http://extjs.com/deploy/dev/docs/?class=Ext.form.ComboBox>`_
 */
Ext.namespace("gxp.form");    

/** api: constructor
 *  .. class:: PalybackModeComboBox(config)
 *   
 *      A combo box for selecting the playback mode of temporal layer(s).
 */
gxp.form.PlaybackModeComboBox = Ext.extend(Ext.form.ComboBox, {
    
    /** i18n */
    modeFieldText: 'Playback Mode',
    normalOptText: 'Normal',
    cumulativeOptText: 'Cumulative',
    rangedOptText: 'Ranged',
    
    
    /** private: property[modes]
     *  ``Array``
     *  List of playback mode options to choose from.
     */
    modes: [], //purposefully adding this to prototype
    
    /** api: property[defaultMode]
     *  ``String``
     *  The value of ``modes`` item to select by default.
     *  Default is ``false`` ('Normal' mode)
     */
    defaultMode: false,
    
    /** api: property[timeAgents]
     *  ``Array``(``OpenLayers.TimeAgent``)
     *  The array of time agents that this combo box will modify
     */
    timeAgents: null,

    allowBlank: false,

    mode: "local",

    triggerAction: "all",

    editable: false,
    
    constructor: function(config){
        this.addEvents({
            /** api: event[modechange]
             *  Fired when the playback mode changes.
             *
             *  Listener arguments:
             *
             *  * field - :class:`gxp.form.PlaybackModeComboBox` This field.
             *  * mode - :``String`` The selected mode value
             *  * agents - :class:`OpenLayers.TimeAgent` An array of the time agents effected
             */
            "modechange" : true
        });
        //initialize the default modes
        if(!config.modes && !this.modes.length){
            this.modes.push([false, this.normalOptText], ['cumulative', this.cumulativeOptText], ['ranged', this.rangedOptText]);
        }
        gxp.form.PlaybackModeComboBox.superclass.constructor.call(this,config);
  },
    initComponent: function() {
        var modes = this.modes; 
        var defaultMode = this.defaultMode;
        
        var defConfig = {
            displayField : "field2",
            valueField : "field1",
            store : modes,
            value : defaultMode,
            listeners : {
                'select' : this.setPlaybackMode,
                scope : this
            }
        };

        Ext.applyIf(this, defConfig);
        
        gxp.form.PlaybackModeComboBox.superclass.initComponent.call(this);
    },
    
    setPlaybackMode: function(combo, record, index){
        if(!this.timeAgents){
            this.timeAgents = this.guessTimeAgents();
        }
        var mode = record.get('field1');
        Ext.each(this.timeAgents,function(agent){
            agent.rangeMode = mode;            
            if(mode == 'range') {
                if(!agent.rangeInterval) {
                    agent.rangeInterval = 1;
                }
            }
        });
        this.fireEvent('modechange',this,mode,this.timeAgents);
    },
    
    /**
     * private: guessTimeAgents
     * Guesses the mapPanel and the ``OpenLayers.Control.TimeManager``
     * and returns an array of all the ``OpenLayers.TimeAgent`` managed by it
     * 
     * return: ``Array``(``OpenLayers.TimeAgent``) 
     */
    guessTimeAgents: function(){
        
    }
    
});

/** api: xtype = gxp_fontcombo */
Ext.reg("gxp_playbackmodecombo", gxp.form.PlaybackModeComboBox);
