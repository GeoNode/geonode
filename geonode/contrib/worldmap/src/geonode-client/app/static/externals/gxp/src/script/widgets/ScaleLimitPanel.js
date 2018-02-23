/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @include widgets/tips/SliderTip.js
 */

/** api: (define)
 *  module = gxp
 *  class = ScaleLimitPanel
 *  base_link = `Ext.Panel <http://extjs.com/deploy/dev/docs/?class=Ext.Panel>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: ScaleLimitPanel(config)
 *   
 *      A panel for assembling scale constraints in SLD styles.
 */
gxp.ScaleLimitPanel = Ext.extend(Ext.Panel, {
    
    /** api: config[maxScaleDenominatorLimit]
     *  ``Number`` Upper limit for scale denominators.  Default is what you get
     *     when you project the world in Spherical Mercator onto a single
     *     256 x 256 pixel tile and assume OpenLayers.DOTS_PER_INCH (this
     *     corresponds to zoom level 0 in Google Maps).
     */
    maxScaleDenominatorLimit: 40075016.68 * 39.3701 * OpenLayers.DOTS_PER_INCH / 256,
    
    /** api: config[limitMaxScaleDenominator]
     *  ``Boolean`` Limit the maximum scale denominator.  If false, no upper
     *     limit will be imposed.
     */
    limitMaxScaleDenominator: true,

    /** api: config[maxScaleDenominator]
     *  ``Number`` The initial maximum scale denominator.  If <limitMaxScaleDenominator> is
     *     true and no minScaleDenominator is provided, <maxScaleDenominatorLimit> will
     *     be used.
     */
    maxScaleDenominator: undefined,

    /** api: config[minScaleDenominatorLimit]
     *  ``Number`` Lower limit for scale denominators.  Default is what you get when
     *     you assume 20 zoom levels starting with the world in Spherical
     *     Mercator on a single 256 x 256 tile at zoom 0 where the zoom factor
     *     is 2.
     */
    minScaleDenominatorLimit: Math.pow(0.5, 19) * 40075016.68 * 39.3701 * OpenLayers.DOTS_PER_INCH / 256,

    /** api: config[limitMinScaleDenominator]
     *  ``Boolean`` Limit the minimum scale denominator.  If false, no lower
     *     limit will be imposed.
     */
    limitMinScaleDenominator: true,

    /** api: config[minScaleDenominator]
     *  ``Number`` The initial minimum scale denominator.  If <limitMinScaleDenominator> is
     *     true and no minScaleDenominator is provided, <minScaleDenominatorLimit> will
     *     be used.
     */
    minScaleDenominator: undefined,
    
    /** api: config[scaleLevels]
     *  ``Number`` Number of scale levels to assume.  This is only for scaling
     *     values exponentially along the slider.  Scale values are not
     *     required to one of the discrete levels.  Default is 20.
     */
    scaleLevels: 20,
    
    /** api: config[scaleSliderTemplate]
     *  ``String`` Template for the tip displayed by the scale threshold slider.
     *
     *  Can be customized using the following keywords in curly braces:
     *
     *  * zoom - the zoom level
     *  * scale - the scale denominator
     *  * type - "Max" or "Min" denominator
     *  * scaleType - "Min" or "Max" scale (sense is opposite of type)
     *
     *  Default is "{scaleType} Scale 1:{scale}".
     */
    scaleSliderTemplate: "{scaleType} Scale 1:{scale}",
    
    /** api: config[modifyScaleTipContext]
     *  ``Function`` Called from the multi-slider tip's getText function.  The
     *     function will receive two arguments - a reference to the panel and
     *     a data object.  The data object will have scale, zoom, and type
     *     properties already calculated.  Other properties added to the data
     *     object  are available to the <scaleSliderTemplate>.
     */
    modifyScaleTipContext: Ext.emptyFn,

    /** private: property[scaleFactor]
     *  ``Number`` Calculated base for determining exponential scaling of values
     *     for the slider.
     */
    scaleFactor: null,
    
    /** private: property[changing]
     *  ``Boolean`` The panel is updating itself.
     */
    changing: false,
    
    border: false,
    
    /** i18n */
    maxScaleLimitText: "Max scale limit",
    minScaleLimitText: "Min scale limit",
    
    /** private: method[initComponent]
     */
    initComponent: function() {
        
        this.layout = "column";
        
        this.defaults = {
            border: false,
            bodyStyle: "margin: 0 5px;"
        };
        this.bodyStyle = {
            padding: "5px"
        };
        
        this.scaleSliderTemplate = new Ext.Template(this.scaleSliderTemplate);
        
        Ext.applyIf(this, {
            minScaleDenominator: this.minScaleDenominatorLimit,
            maxScaleDenominator: this.maxScaleDenominatorLimit
        });
        
        this.scaleFactor = Math.pow(
            this.maxScaleDenominatorLimit / this.minScaleDenominatorLimit,
            1 / (this.scaleLevels - 1)
        );
        
        this.scaleSlider = new Ext.Slider({
            vertical: true,
            height: 100,
            values: [0, 100],
            listeners: {
                changecomplete: function(slider, value) {
                    this.updateScaleValues(slider);
                },
                render: function(slider) {
                    slider.thumbs[0].el.setVisible(this.limitMaxScaleDenominator);
                    slider.thumbs[1].el.setVisible(this.limitMinScaleDenominator);
                    slider.setDisabled(!this.limitMinScaleDenominator && !this.limitMaxScaleDenominator);
                },
                scope: this
            },
            plugins: [new gxp.slider.Tip({
                getText: (function(thumb) {
                    var index = thumb.slider.thumbs.indexOf(thumb);
                    var value = thumb.value;
                    var scales = this.sliderValuesToScale([thumb.value]);
                    var data = {
                        scale: String(scales[0]),
                        zoom: (thumb.value * (this.scaleLevels / 100)).toFixed(1),
                        type: (index === 0) ? "Max" : "Min",
                        scaleType: (index === 0) ? "Min" : "Max"
                    };
                    this.modifyScaleTipContext(this, data);
                    return this.scaleSliderTemplate.apply(data);
                }).createDelegate(this)
            })]
        });
        
        this.maxScaleDenominatorInput = new Ext.form.NumberField({
            allowNegative: false,
            width: 100,
            fieldLabel: "1",
            value: Math.round(this.maxScaleDenominator),
            disabled: !this.limitMaxScaleDenominator,
            validator: (function(value) {
                return !this.limitMinScaleDenominator || (value > this.minScaleDenominator);
            }).createDelegate(this),
            listeners: {
                valid: function(field) {
                    var value = Number(field.getValue());
                    var limit = Math.round(this.maxScaleDenominatorLimit);
                    if(value < limit && value > this.minScaleDenominator) {
                        this.maxScaleDenominator = value;
                        this.updateSliderValues();
                    }
                },
                change: function(field) {
                    var value = Number(field.getValue());
                    var limit = Math.round(this.maxScaleDenominatorLimit);
                    if(value > limit) {
                        field.setValue(limit);
                    } else if(value < this.minScaleDenominator) {
                        field.setValue(this.minScaleDenominator);
                    } else {
                        this.maxScaleDenominator = value;
                        this.updateSliderValues();
                    }
                },
                scope: this
            }
        });

        this.minScaleDenominatorInput = new Ext.form.NumberField({
            allowNegative: false,
            width: 100,
            fieldLabel: "1",
            value: Math.round(this.minScaleDenominator),
            disabled: !this.limitMinScaleDenominator,
            validator: (function(value) {
                return !this.limitMaxScaleDenominator || (value < this.maxScaleDenominator);
            }).createDelegate(this),
            listeners: {
                valid: function(field) {
                    var value = Number(field.getValue());
                    var limit = Math.round(this.minScaleDenominatorLimit);
                    if(value > limit && value < this.maxScaleDenominator) {
                        this.minScaleDenominator = value;
                        this.updateSliderValues();
                    }
                },
                change: function(field) {
                    var value = Number(field.getValue());
                    var limit = Math.round(this.minScaleDenominatorLimit);
                    if(value < limit) {
                        field.setValue(limit);
                    } else if(value > this.maxScaleDenominator) {
                        field.setValue(this.maxScaleDenominator);
                    } else {
                        this.minScaleDenominator = value;
                        this.updateSliderValues();
                    }
                },
                scope: this
            }
        });
        
        this.items = [this.scaleSlider, {
            xtype: "panel",
            layout: "form",
            defaults: {border: false},
            items: [{
                labelWidth: 90,
                layout: "form",
                width: 150,
                items: [{
                    xtype: "checkbox",
                    checked: !!this.limitMinScaleDenominator,
                    fieldLabel: this.maxScaleLimitText,
                    listeners: {
                        check: function(box, checked) {
                            this.limitMinScaleDenominator = checked;
                            var slider = this.scaleSlider;
                            slider.setValue(1, 100);
                            slider.thumbs[1].el.setVisible(checked);
                            this.minScaleDenominatorInput.setDisabled(!checked);
                            this.updateScaleValues(slider);
                            slider.setDisabled(!this.limitMinScaleDenominator && !this.limitMaxScaleDenominator);
                        },
                        scope: this
                    }
                }]
            }, {
                labelWidth: 10,
                layout: "form",
                items: [this.minScaleDenominatorInput]
            }, {
                labelWidth: 90,
                layout: "form",
                items: [{
                    xtype: "checkbox",
                    checked: !!this.limitMaxScaleDenominator,
                    fieldLabel: this.minScaleLimitText,
                    listeners: {
                        check: function(box, checked) {
                            this.limitMaxScaleDenominator = checked;
                            var slider = this.scaleSlider;
                            slider.setValue(0, 0);
                            slider.thumbs[0].el.setVisible(checked);
                            this.maxScaleDenominatorInput.setDisabled(!checked);
                            this.updateScaleValues(slider);
                            slider.setDisabled(!this.limitMinScaleDenominator && !this.limitMaxScaleDenominator);
                        },
                        scope: this
                    }
                }]
            }, {
                labelWidth: 10,
                layout: "form",
                items: [this.maxScaleDenominatorInput]
            }]
        }];

        this.addEvents(
            /**
             * Event: change
             * Fires before any field blurs if the field value has changed.
             *
             * Listener arguments:
             * symbolizer - {Object} A symbolizer with fill related properties
             *     updated.
             */
            "change"
        ); 

        gxp.ScaleLimitPanel.superclass.initComponent.call(this);
        
    },
    
    /** private: method[updateScaleValues]
     */
    updateScaleValues: function(slider) {
        if(!this.changing) {
            var values = slider.getValues();
            var resetSlider = false;
            if(!this.limitMaxScaleDenominator) {
                if(values[0] > 0) {
                    values[0] = 0;
                    resetSlider = true;
                }
            }
            if(!this.limitMinScaleDenominator) {
                if(values[1] < 100) {
                    values[1] = 100;
                    resetSlider = true;
                }
            }
            if(resetSlider) {
                slider.setValue(0, values[0]);
                slider.setValue(1, values[1]);
            } else {
                var scales = this.sliderValuesToScale(values);
                var max = scales[0];
                var min = scales[1];
                this.changing = true;
                this.minScaleDenominatorInput.setValue(min);
                this.maxScaleDenominatorInput.setValue(max);
                this.changing = false;
                this.fireEvent(
                    "change", this,
                    (this.limitMinScaleDenominator) ? min : undefined,
                    (this.limitMaxScaleDenominator) ? max : undefined
                );
            }
        }
    },
    
    /** private: method[updateSliderValues]
     */
    updateSliderValues: function() {
        if(!this.changing) {
            var min = this.minScaleDenominator;
            var max = this.maxScaleDenominator;
            var values = this.scaleToSliderValues([max, min]);
            this.changing = true;
            this.scaleSlider.setValue(0, values[0]);
            this.scaleSlider.setValue(1, values[1]);
            this.changing = false;
            this.fireEvent(
                "change", this,
                (this.limitMinScaleDenominator) ? min : undefined,
                (this.limitMaxScaleDenominator) ? max : undefined
            );
        }
    },

    /** private: method[sliderValuesToScale]
     *  :arg values: ``Array`` Values from the scale slider.
     *  :return: ``Array`` A two item array of min and max scale denominators.
     *  
     *  Given two values between 0 and 100, generate the min and max scale
     *  denominators.  Assuming exponential scaling with <scaleFactor>.
     */
    sliderValuesToScale: function(values) {
        var interval = 100 / (this.scaleLevels - 1);
        return [Math.round(Math.pow(this.scaleFactor, (100 - values[0]) / interval) * this.minScaleDenominatorLimit),
                Math.round(Math.pow(this.scaleFactor, (100 - values[1]) / interval) * this.minScaleDenominatorLimit)];
    },
    
    /** private: method[scaleToSliderValues]
     */
    scaleToSliderValues: function(scales) {
        var interval = 100 / (this.scaleLevels - 1);
        return [100 - (interval * Math.log(scales[0] / this.minScaleDenominatorLimit) / Math.log(this.scaleFactor)),
                100 - (interval * Math.log(scales[1] / this.minScaleDenominatorLimit) / Math.log(this.scaleFactor))];
    }
    
});

/** api: xtype = gxp_scalelimitpanel */
Ext.reg('gxp_scalelimitpanel', gxp.ScaleLimitPanel); 
