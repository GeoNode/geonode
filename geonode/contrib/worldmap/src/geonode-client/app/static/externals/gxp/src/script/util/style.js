/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @require util/color.js
 */

Ext.ns("gxp.util");

/**
 * Based on functions from https://github.com/tschaub/geoscript-js
 */
gxp.util.style = (function() {
    
    var exports = {},
        hsl2rgb = gxp.util.color.hsl2rgb,
        rgb2hsl = gxp.util.color.rgb2hsl,
        rgb = gxp.util.color.rgb,
        hex = gxp.util.color.hex,
        colorRegEx = /Color$/,
        literalRegEx = /(Width|Height|[rR]otation|Opacity|Size)$/;
    
    /** api: function[interpolateSymbolizers]
     *  :arg start: ``Array`` Array of ``OpenLayers.Symbolizer`` instances
     *  :arg end: ``Array`` Array of ``OpenLayers.Symbolizer`` instances
     *  :arg fraction: ``Float`` Number between 0 and 1, which is the distance
     *      between ``start`` and ``end``
     *  :returns: ``Array`` Array of ``OpenLayers.Symbolizer instances
     *
     *  Interpolates an array of symbolizers between start and end values.
     */
    exports.interpolateSymbolizers = function(start, end, fraction) {
        var startSymbolizer, endSymbolizer;
        var parts = [];
        for (var i=0, ii=start.length; i<ii; ++i) {
            startSymbolizer = start[i];
            endSymbolizer = end[i];
            if (!endSymbolizer) {
                throw new Error("Start style and end style must have equal number of parts.");
            }
            parts[i] = interpolateSymbolizer(startSymbolizer, endSymbolizer, fraction);
        }
        return parts;
    };

    function interpolateSymbolizer(startSymbolizer, endSymbolizer, fraction) {
        var symbolizer = Ext.apply({}, startSymbolizer);
        Ext.iterate(startSymbolizer, function(key) {
            if (colorRegEx.test(key)) {
                var startHSL = rgb2hsl(rgb(startSymbolizer[key])),
                    endHSL = rgb2hsl(rgb(endSymbolizer[key]));
                if (startHSL && endHSL) {
                    var hsl = [];
                    for (var i=startHSL.length-1; i>=0; --i) {
                        hsl[i] = startHSL[i] + (fraction * (endHSL[i] - startHSL[i]));
                    }
                    symbolizer[key] = hex(hsl2rgb(hsl));
                }
            } else if (literalRegEx.test(key)) {
                var literal = interpolateLiteral(key, startSymbolizer, endSymbolizer, fraction);
                if (literal !== null) {
                    symbolizer[key] = literal;
                }
            }
        });
        return symbolizer;
    }

    function interpolateLiteral(property, startSymbolizer, endSymbolizer, fraction) {
        var literal = null;
        if ((property in startSymbolizer) && (property in endSymbolizer)) {
            var startValue = startSymbolizer[property];
            var endValue = endSymbolizer[property];
            if (startValue.literal && endValue.literal) {
                startValue = parseFloat(startValue.text);
                endValue = parseFloat(endValue.text);
                literal = startValue + (fraction * (endValue - startValue));
            }
        }
        return literal;
    }
    
    return exports;
})();