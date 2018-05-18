/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp.form
 *  class = ColorField
 *  base_link = `Ext.form.TextField <http://extjs.com/deploy/dev/docs/?class=Ext.form.TextField>`_
 */
Ext.namespace("gxp.form");

/** api: constructor
 *  .. class:: ColorField(config)
 *   
 *      A text field that colors its own background based on the input value.
 *      The value may be any one of the 16 W3C supported CSS color names
 *      (http://www.w3.org/TR/css3-color/).  The value can also be an arbitrary
 *      RGB hex value prefixed by a '#' (e.g. '#FFCC66').
 */
gxp.form.ColorField = Ext.extend(Ext.form.TextField,  {

    /** api: property[cssColors]
     *  ``Object``
     *  Properties are supported CSS color names.  Values are RGB hex strings
     *  (prefixed with '#').
     */
    cssColors: {
        aqua: "#00FFFF",
        black: "#000000",
        blue: "#0000FF",
        fuchsia: "#FF00FF",
        gray: "#808080",
        green: "#008000",
        lime: "#00FF00",
        maroon: "#800000",
        navy: "#000080",
        olive: "#808000",
        purple: "#800080",
        red: "#FF0000",
        silver: "#C0C0C0",
        teal: "#008080",
        white: "#FFFFFF",
        yellow: "#FFFF00"
    },
    
    /** api: config[defaultBackground]
     *  The default background color if the symbolizer has no fillColor set.
     *  Defaults to #ffffff.
     */
    defaultBackground: "#ffffff",

    /** private: method[initComponent]
     *  Override
     */
    initComponent: function() {
        if (this.value) {
            this.value = this.hexToColor(this.value);
        }
        gxp.form.ColorField.superclass.initComponent.call(this);
        
        // Add the colorField listener to color the field.
        this.on({
            render: this.colorField,
            valid: this.colorField,
            scope: this
        });
        
    },
    
    /** private: method[isDark]
     *  :arg hex: ``String`` A RGB hex color string (prefixed by '#').
     *  :returns: ``Boolean`` The color is dark.
     *  
     *  Determine if a color is dark by avaluating brightness according to the
     *  W3C suggested algorithm for calculating brightness of screen colors.
     *  http://www.w3.org/WAI/ER/WD-AERT/#color-contrast
     */
    isDark: function(hex) {
        var dark = false;
        if(hex) {
            // convert hex color values to decimal
            var r = parseInt(hex.substring(1, 3), 16) / 255;
            var g = parseInt(hex.substring(3, 5), 16) / 255;
            var b = parseInt(hex.substring(5, 7), 16) / 255;
            // use w3C brightness measure
            var brightness = (r * 0.299) + (g * 0.587) + (b * 0.144);
            dark = brightness < 0.5;
        }
        return dark;
    },
    
    /** private: method[colorField]
     *  Set the background and font color for the field.
     */
    colorField: function() {
        var color = this.colorToHex(this.getValue()) || this.defaultBackground;
        this.getEl().setStyle({
            "background": color,
            "color": this.isDark(color) ? "#ffffff" : "#000000"
        });
    },
    
    /** api: method[getHexValue]
     *  :returns: ``String`` The RGB hex string for the field's value (prefixed
     *      with '#').
     *  
     *  As a compliment to the field's ``getValue`` method, this method always
     *  returns the RGB hex string representation of the current value
     *  in the field (given a named color or a hex string).
     */
    getHexValue: function() {
        return this.colorToHex(
            gxp.form.ColorField.superclass.getValue.apply(this, arguments));
    },

    /** api: method[getValue]
     *  :returns: ``String`` The RGB hex string for the field's value (prefixed
     *      with '#').
     *  
     *  This method always returns the RGB hex string representation of the
     *  current value in the field (given a named color or a hex string),
     *  except for the case when the value has not been changed.
     */
    getValue: function() {
        var v = this.getHexValue();
        var o = this.initialConfig.value;
        if (v === this.hexToColor(o)) {
            v = o;
        }
        return v;
    },
    
    /** api: method[setValue]
     *  :arg value: ``Object``
     *  
     *  Sets the value of the field. If the value matches one of the well known
     *  colors in ``cssColors``, a human readable value will be displayed
     *  instead of the hex code.
     */
    setValue: function(value) {
        gxp.form.ColorField.superclass.setValue.apply(this,
            [this.hexToColor(value)]);
    },
    
    /** private: method[colorToHex]
     *  :returns: ``String`` A RGB hex color string or null if none found.
     *  
     *  Return the RGB hex representation of a color string.  If a CSS supported
     *  named color is supplied, the hex representation will be returned.
     *  If a non-CSS supported named color is supplied, null will be
     *  returned.  If a RGB hex string is supplied, the same will be returned.
     */
    colorToHex: function(color) {
        if (!color) {
            return color;
        }
        var hex;
        if (color.match(/^#[0-9a-f]{6}$/i)) {
            hex = color;
        } else {
            hex = this.cssColors[color.toLowerCase()] || null;
        }
        return hex;
    },
    
    /** private: method[hexToColor]
     */
    hexToColor: function(hex) {
        if (!hex) {
            return hex;
        }
        var color = hex;
        for (var c in this.cssColors) {
            if (this.cssColors[c] == color.toUpperCase()) {
                color = c;
                break;
            }
        }
        return color;
    }
    
});

Ext.reg("gxp_colorfield", gxp.form.ColorField);
