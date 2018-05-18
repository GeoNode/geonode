/**
 * Copyright (c) 2008-2009 The Open Source Geospatial Foundation
 *
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

Ext.onReady(function(){

    new Ext.slider.SingleSlider({
        renderTo: "tip-slider",
        width: 214,
        minValue: 0,
        maxValue: 100,
        plugins: new GeoExt.SliderTip()
    });

    new Ext.slider.SingleSlider({
        renderTo: "custom-tip-slider",
        width: 214,
        increment: 10,
        minValue: 0,
        maxValue: 100,
        plugins: new GeoExt.SliderTip({
            getText: function(thumb){
                return String.format("<b>{0}% complete</b>", thumb.value);
            }
        })
    });

    new Ext.slider.SingleSlider({
        renderTo: "no-hover-tip",
        width: 214,
        increment: 10,
        minValue: 0,
        maxValue: 100,
        plugins: new GeoExt.SliderTip({hover: false})
    });
    
    new Ext.slider.MultiSlider({
        renderTo: "multi-slider-horizontal",
        width   : 214,
        minValue: 0,
        maxValue: 100,
        values  : [10, 50, 90],
        plugins : new GeoExt.SliderTip()
    });
    
    new Ext.slider.MultiSlider({
        renderTo : "multi-slider-vertical",
        vertical : true,
        height   : 214,
        minValue: 0,
        maxValue: 100,
        values  : [10, 50, 90],
        plugins : new GeoExt.SliderTip()
    });
});
