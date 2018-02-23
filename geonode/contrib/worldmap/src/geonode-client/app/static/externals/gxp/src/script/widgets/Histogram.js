/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp
 *  class = Histogram
 *  base_link = `Ext.BoxComponent <http://extjs.com/deploy/dev/docs/?class=Ext.BoxComponent>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: Histogram(config)
 *   
 *      A component for displaying a simple histogram. Quantities will always
 *      be stretched so the highest quantity takes up 100% of the available
 *      height.
 *
 *      .. code-block:: javascript
 *
 *          new gxp.Histogram({
 *              quantities: [1,2,3,4,5,4,3,2,1],
 *              renderTo: document.body
 *          });
 */
gxp.Histogram = Ext.extend(Ext.BoxComponent, {
    
    /** api: config[quantities]
     *  ``Array(Number)`` Array of quantities for the histogram.
     */
        
    /** private: method[onRender]
     */
    onRender: function(ct, position) {
        if (!this.el) {
            var el = document.createElement("div");
            el.id = this.getId();
            this.el = Ext.get(el);
        }
        this.el.addClass("gxp-histogram");
        if (this.quantities) {
            this.setQuantities(this.quantities);
        }
        gxp.Histogram.superclass.onRender.apply(this, arguments);
    },
    
    /** api: method[setQuantities]
     *  :arg quantities: ``Array(Number)`` Array of quantities for the
     *      histogram.
     *
     *  Updates the quantities that were originally configured with
     *  :obj:`quantities`.
     */
    setQuantities: function(quantities) {
        this.quantities = quantities;

        while (this.el.dom.firstChild) {
            this.el.dom.removeChild(this.el.dom.firstChild);
        }
        
        var quantity,
            max = 0, min = Number.POSITIVE_INFINITY,
            i, ii = quantities.length;
        for (i=0; i<ii; ++i) {
            quantity = quantities[i];
            if (quantity < min) {
                min = quantity;
            }
            if (quantity > max) {
                max = quantity;
            }
        }
        
        var bar, factor = 100 / max,
            style, height, width = (100 / ii);
        for (i=0; i<ii; ++i) {
            bar = document.createElement("div");
            bar.className = "bar";
            style = bar.style;
            style.width = width + "%";
            style.left = (i * width) + "%";
            style.top = (100 - (quantities[i] - min) * factor) + "%";
            this.el.dom.appendChild(bar);
        }
    }

});

/** api: xtype = gxp_histogram */
Ext.reg("gxp_histogram", gxp.Histogram);
