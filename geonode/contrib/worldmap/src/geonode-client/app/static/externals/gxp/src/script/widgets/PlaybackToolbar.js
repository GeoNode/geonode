/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires OpenLayers/Control/TimeManager.js
 * @requires OpenLayers/TimeAgent.js
 * @requires widgets/slider/TimeSlider.js
 */

/** api: (define)
 *  module = gxp
 *  class = PlaybackToolbar
 *  base_link = `Ext.Toolbar <http://dev.sencha.com/deploy/dev/docs/?class=Ext.Toolbar>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: PlaybackToolbar(config)
 *   
 *      Create a panel for showing a ScaleLine control and a combobox for 
 *      selecting the map scale.
 */
gxp.PlaybackToolbar = Ext.extend(Ext.Toolbar, {
    
    /** api: config[control]
     *  ``OpenLayers.Control`` or :class:`OpenLayers.Control.TimeManager`
     *  The control to configure the playback panel with.
     */
    control: null,
    viewer: null,
    initialTime:null,
    timeFormat:"l, F d, Y g:i:s A",
    toolbarCls:'x-toolbar gx-overlay-playback', //must use toolbarCls since it is used instead of baseCls in toolbars
    ctCls: 'gx-playback-wrap',
    slider:true,
    dynamicRange:false,
    //api config
    //playback mode is one of: "track","cumulative","ranged",??"decay"??
    playbackMode:"track",
    showIntervals:false,
    labelButtons:false,
    settingsButton:true,
    rateAdjuster:false,
    looped:false,
    autoPlay:false,
    //api config ->timeDisplayConfig:null,
    //api property
    optionsWindow:null,
    /** api: property[playing]
     * ``Boolean``
     * Boolean flag indicating the control is currently playing or not.
     * Read-only
     */
    playing: false,
    // api config
    //playbackActions, default: ["settings","reset","play","fastforward","next","loop"]; also available are "pause" and "end"
    
    //i18n
    /** api: config[playLabel]
     *  ``String``
     *  Text for play button label (i18n).
     */
    playLabel:'Play',
    /** api: config[playTooltip]
     *  ``String``
     *  Text for play button tooltip (i18n).
     */
    playTooltip:'Play',
    stopLabel:'Stop',
    stopTooltip:'Stop',
    fastforwardLabel:'FFWD',
    fastforwardTooltip:'Double Speed Playback',
    nextLabel:'Next',
    nextTooltip:'Advance One Frame',
    resetLabel:'Reset',
    resetTooltip:'Reset to the start',
    loopLabel:'Loop',
    loopTooltip:'Continously loop the animation',
    normalTooltip:'Return to normal playback',
    pauseLabel:'Pause',
    pauseTooltip:'Pause',

    /** private: method[initComponent]
     *  Initialize the component.
     */
    initComponent: function() {
        if(!this.playbackActions){
            this.playbackActions = ["settings","slider","reset","play","fastforward","next","loop"]; 
        }
        if(!this.control){
            this.control = this.buildTimeManager();
        }
        this.control.events.on({
            'play':function(evt){
                this.playing = true;
            },
            'stop':function(evt){
                this.playing = false;
            },
            scope: this
        });
        
        this.availableTools = Ext.applyIf(this.availableTools || {}, this.getAvailableTools());
        
        Ext.applyIf(this,{
            defaults:{xtype:'button',flex:1,scale:'small'},
            items:this.buildPlaybackItems(),
            border:false,
            frame:false,
            unstyled:true,
            shadow:false,
            timeDisplayConfig:{'xtype':'tip',format:this.timeFormat,height:'auto',closeable:false,title:false,width:210}
        });
        this.addEvents(
            /**
             * Event: timechange
             * Fires when the current time represented changes.
             *
             * Listener arguments:
             * toolbar - {gxp.plugin.PlaybackToolbar} This playback toolbar
             * currentTime - {Date} The current time represented in the TimeManager control
             *      attached to this toolbar
             */
            "timechange",
            /**
             * Event: rangemodified
             * Fires when the start and/or end times of the slider change
             *
             * Listener arguments:
             * toolbar - {gxp.plugin.PlaybackToolbar} This playback toolbar
             * range - {Array(Date)} The current time range for playback allowed in the
             *      TimeManager control attached to this toolbar
             */
            "rangemodified"            
        );
        gxp.PlaybackToolbar.superclass.initComponent.call(this);        
    },
    /** private: method[destroy]
     *  Destory the component.
     */
    destroy: function(){
        //kill the control but only if we created the control
        if(this.control && !this.initialConfig.control){
            this.control.map && this.control.map.removeControl(this.control);
            this.control.destroy();
            this.control = null;
        }
        gxp.PlaybackToolbar.superclass.destroy.call(this);
    },
    /** api: method[setTime]
     *  :arg time: {Date}
     *  :return: {Boolean} - true if the time could be set to the supplied value
     *          false if the time is outside the current range of the TimeManager
     *          control.
     *          
     *  Set the time represented by the playback toolbar programatically
     */
    setTime: function(time){
        var timeVal = time.getTime();
        if(timeVal<this.slider.minValue || timeVal>this.slider.maxValue){
            return false;
        }else{
            this.control.setTime(time);
            return true;
        }
    },
    /** api: method[setTimeFormat]
     *  :arg format: {String}
     *  
     *  Set the format string used by the time slider tooltip
     */    
    setTimeFormat: function(format){
        if(format){
            this.timeFormat = format;
            this.slider.setTimeFormat(format);
        }
    },
    /** api: method[setPlaybackMode]
     * :arg mode: {String} one of 'track',
     * 'cumulative', or 'ranged'
     *  
     *  Set the playback mode of the control.
     */
    setPlaybackMode: function(mode){
        if(mode){
            this.playbackMode = mode;
            this.slider.setPlaybackMode(mode);
        }
    },

    /** private: method[buildPlaybackItems] */
    buildPlaybackItems: function(){
        var tools = this.playbackActions;
        var items =[];
        for(var i=0,len=tools.length;i<len;i++){
            var key = tools[i];
            var tool = this.availableTools[key];
            if(tool){
                items.push(tool);
            } else {
                if(['|',' ','->'].indexOf(key)>-1){
                    items.push(key);
                }
            }
        }
        return items;
    },

    getAvailableTools: function(){         
        var tools = {
            'slider': {
                xtype: 'gxp_timeslider',
                ref: 'slider',
                timeManager: this.control,
                playbackMode: this.playbackMode
            },
            'reset': {
                iconCls: 'gxp-icon-reset',
                ref:'btnReset',
                handler: this.control.reset,
                scope: this.control,
                tooltip: this.resetTooltip,
                menuText: this.resetLabel,
                text: (this.labelButtons) ? this.resetLabel : false
            },
            'pause': {
                iconCls: 'gxp-icon-pause',
                ref:'btnPause',
                handler: this.control.stop,
                scope: this.control,
                tooltip: this.stopTooltip,
                menuText: this.stopLabel,
                text: (this.labelButtons) ? this.stopLabel : false,
                toggleGroup: 'timecontrol',
                enableToggle: true,
                allowDepress: false
            },
            'play': {
                iconCls: 'gxp-icon-play',
                ref:'btnPlay',
                toggleHandler: this.toggleAnimation,
                scope: this,
                toggleGroup: 'timecontrol',
                enableToggle: true,
                allowDepress: true,
                tooltip: this.playTooltip,
                menuText: this.playLabel,
                text: (this.labelButtons) ? this.playLabel : false
            },
            'next': {
                iconCls: 'gxp-icon-next',
                ref:'btnNext',
                handler: function(){
                    this.stop();
                    this.tick();
                },
                scope: this.control,
                tooltip: this.nextTooltip,
                menuText: this.nextLabel,
                text: (this.labelButtons) ? this.nextLabel : false
            },
            'end': {
                iconCls: 'gxp-icon-last',
                ref:'btnEnd',
                handler: this.forwardToEnd,
                scope: this,
                tooltip: this.endTooltip,
                menuText: this.endLabel,
                text: (this.labelButtons) ? this.endLabel : false
            },
            'loop': {
                iconCls: 'gxp-icon-loop',
                ref:'btnLoop',
                tooltip: this.loopTooltip,
                enableToggle: true,
                allowDepress: true,
                pressed: this.looped,
                toggleHandler: this.toggleLoopMode,
                scope: this,
                menuText: this.loopLabel,
                text: (this.labelButtons) ? this.loopLabel : false
            },
            'fastforward': {
                iconCls: 'gxp-icon-ffwd',
                ref:'btnFastforward',
                tooltip: this.fastforwardTooltip,
                enableToggle: true,
                //allowDepress: true,
                toggleGroup: 'fastforward',
                toggleHandler: this.toggleDoubleSpeed,
                scope: this,
                disabled:true,
                menuText: this.fastforwardLabel,
                text: (this.labelButtons) ? this.fastforwardLabel : false
            },
            'settings': {
                iconCls: 'gxp-icon-settings',
                ref:'btnSettings',
                scope: this,
                handler:this.toggleOptionsWindow,
                enableToggle:false,
                tooltip: this.settingsTooltip,
                menuText: this.settingsLabel,
                text: (this.labelButtons) ? this.settingsLabel : false
            }
        };
        return tools;
    },

    buildTimeManager:function() {
        this.controlConfig || (this.controlConfig = {});
        //test for bad range times
        if(this.controlConfig.range && this.controlConfig.range.length) {
            for(var i = 0; i < this.controlConfig.range.length; i++) {
                var dateString = this.controlConfig.range[i];
                if(dateString.indexOf('T') > -1 && dateString.indexOf('Z') == -1) {
                    dateString = dateString.substring(0, dateString.indexOf('T'));
                }
                this.controlConfig.range[i] = dateString;
            }
        }
        // Test for and deal with pre-configured timeAgents & layers
        if(this.controlConfig.timeAgents) {
            for(var i = 0; i < this.controlConfig.timeAgents.length; i++) {
                var config = this.controlConfig.timeAgents[i];
                var agentClass = config.type;
                var layers = [];
                //put real layers, not references here
                Ext.each(config.layers, function(lyrJson) {
                    //source & name identify different layers, but title & styles
                    //are required to distinguish the same layer added multiple times with a different
                    //style or presentation
                    var ndx = app.mapPanel.layers.findBy(function(rec) {
                        return rec.json && 
                        rec.json.source == lyrJson.source &&
                        rec.json.title == lyrJson.title &&
                        rec.json.name == lyrJson.name &&
                        (rec.json.styles == lyrJson.styles ||
                            !!rec.json.styles == false && !!lyrJson.styles == false);
                    });

                    if(ndx > -1) {
                        layers.push(app.mapPanel.layers.getAt(ndx).getLayer());
                    }
                });

                config.layers = layers;
                delete config.type;
                //TODO handle subclasses of TimeAgent subclasses
                var agent = agentClass ? new OpenLayers.TimeAgent[agentClass](config) : new OpenLayers.TimeAgent(config);
                this.controlConfig.timeAgents[i] = agent;
            }
        }
        else {
            if(this.playbackMode == 'ranged') {
                Ext.apply(this.controlConfig, {
                    agentOptions : {
                        'WMS' : {
                            rangeMode : 'range',
                            rangeInterval : this.rangedPlayInterval
                        },
                        'Vector' : {
                            rangeMode : 'range',
                            rangeInterval : this.rangedPlayInterval
                        }
                    }
                });
            }
            else if(this.playbackMode == 'cumulative') {
                Ext.apply(this.controlConfig, {
                    agentOptions : {
                        'WMS' : {
                            rangeMode : 'cumulative'
                        },
                        'Vector' : {
                            rangeMode : 'cumulative'
                        }
                    }
                });
            }
        }
        //DON'T DROP FRAMES
        //this.controlConfig.maxFrameDelay = NaN;
        var ctl = this.control = new OpenLayers.Control.TimeManager(this.controlConfig);
        ctl.loop = this.looped;
        this.mapPanel.map.addControl(ctl);
        if(ctl.layers) {
            this.fireEvent('rangemodified', this, ctl.range);
        }
        return ctl;
    },
    
/** BUTTON HANDLERS **/    
    forwardToEnd: function(btn){
        var ctl = this.control;
        ctl.setTime(new Date(ctl.range[(ctl.step < 0) ? 0 : 1].getTime()));
    },
    toggleAnimation:function(btn,pressed){
        if(!btn.bound && pressed){
            this.control.events.on({
                'stop':function(evt){
                    btn.toggle(false);
                    if(evt.rangeExceeded){
                        this._resetOnPlay = true;
                    }
                },
                'play':function(evt){
                    btn.toggle(true);
                    if(this._resetOnPlay){
                        this.reset();
                        delete this._resetOnPlay;
                    }
                }
            });
            btn.bound=true;
        }
        
        if(pressed){
            if(!this.control.timer){
                //don't start playing again if it is already playing
                this.control.play();
            }
            btn.btnEl.removeClass('gxp-icon-play');
            btn.btnEl.addClass('gxp-icon-pause');
            btn.setTooltip(this.pauseTooltip);
        } else {
            if(this.control.timer){
                //don't stop playing again if it is already stopped
                this.control.stop();
            }
            btn.btnEl.addClass('gxp-icon-play');
            btn.btnEl.removeClass('gxp-icon-pause');
            btn.setTooltip(this.playTooltip);
        }
        
        btn.el.removeClass('x-btn-pressed');
        btn.refOwner.btnFastforward.setDisabled(!pressed);
        if(this.labelButtons && btn.text){
            btn.setText(pressed?this.pauseLabel:this.playLabel);
        }
    },
    toggleLoopMode:function(btn,pressed){
        this.control.loop=pressed;
        btn.setTooltip(pressed?this.normalTooltip:this.loopTooltip);
        if(this.labelButtons && btn.text){
            btn.setText(pressed?this.normalLabel:this.loopLabel);
        }
    },
    toggleDoubleSpeed:function(btn,pressed){
        var framerate = this.control.frameRate * ((pressed) ? 2 : 0.5);
        this.control.setFrameRate(framerate);
        btn.setTooltip((pressed) ? this.normalTooltip : this.fastforwardTooltip);
    },
    toggleOptionsWindow:function(btn,pressed){
        if(pressed && this.optionsWindow.hidden){
            if(!this.optionsWindow.optionsPanel.timeManager){
                this.optionsWindow.optionsPanel.timeManager = this.control;
                this.optionsWindow.optionsPanel.playbackToolbar = this;
            }
            this.optionsWindow.show();
        }
        else if(!pressed && !this.optionsWindow.hidden){
            this.optionsWindow.hide();
        }
    }
});

/**
 * Static Methods
 */
gxp.PlaybackToolbar.guessTimeFormat = function(increment){
    if (increment) {
        var resolution = gxp.PlaybackToolbar.smartIntervalFormat(increment).units;
        var format = this.timeFormat;
        switch (resolution) {
            case 'Minutes':
                format = 'l, F d, Y g:i A';
                break;
            case 'Hours':
                format = 'l, F d, Y g A';
                break;
            case 'Days':
                format = 'l, F d, Y';
                break;
            case 'Months':
                format = 'F, Y';
                break;
            case 'Years':
                format = 'Y';
                break;
        }
        return format;
    }
};
gxp.PlaybackToolbar.smartIntervalFormat = function(diff){
    var unitText, diffValue, absDiff=Math.abs(diff);
    if(absDiff<5e3){
        unitText='Seconds';
        diffValue=(Math.round(diff/1e2))/10;
    }
    else if(absDiff<35e5){
        unitText='Minutes';
        diffValue=(Math.round(diff/6e2))/10;
    }
    else if(absDiff<828e5){
        unitText='Hours';
        diffValue=(Math.round(diff/36e4))/10;
    }
    else if(absDiff<250e7){
        unitText='Days';
        diffValue=(Math.round(diff/864e4))/10;
    }
    else if(absDiff<311e8){
        unitText='Months';
        diffValue=(Math.round(diff/2628e5))/10;
    }else{
        unitText='Years';
        diffValue=(Math.round(diff/31536e5))/10;
    }
    return {units:unitText,value:diffValue};
};

/** api: xtype = gxp_playbacktoolbar */
Ext.reg('gxp_playbacktoolbar', gxp.PlaybackToolbar);