/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = StyleWriter
 *  base_link = `Ext.util.Observable <http://extjs.com/deploy/dev/docs/?class=Ext.util.Observable>`_
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: StyleWriter(config)
 *   
 *      Base class for plugins that plug into :class:`gxp.WMSStylesDialog` or
 *      similar classes that have a ``layerRecord`` and a ``stylesStore`` with
 *      a ``userStyle`` field. The plugin provides a save method, which will 
 *      persist style changes from the ``stylesStore`` to the server and
 *      associate them with the layer referenced in the target's
 *      ``layerRecord``.
 */
gxp.plugins.StyleWriter = Ext.extend(Ext.util.Observable, {
    
    /** private: property[target]
     *  ``Object``
     *  The object that this plugin is plugged into.
     */
    
    /** api: property[deletedStyles]
     *  ``Array(String)`` style names of styles from the server that were
     *  deleted and have to be removed from the server
     */
    deletedStyles: null,
    
    /** private: method[constructor]
     */
    constructor: function(config) {
        this.initialConfig = config;
        Ext.apply(this, config);
        
        this.deletedStyles = [];
        
        gxp.plugins.StyleWriter.superclass.constructor.apply(this, arguments);
    },
    
    /** private: method[init]
     *  :arg target: ``Object`` The object initializing this plugin.
     */
    init: function(target) {
        this.target = target;
        
        // keep track of removed style records, because Ext.Store does not.
        target.stylesStore.on({
            "remove": function(store, record, index) {
                var styleName = record.get("name");
                // only proceed if the style comes from the server
                record.get("name") === styleName &&
                    this.deletedStyles.push(styleName);
            },
            scope: this
        });
        
        target.on({
            "beforesaved": this.write,
            scope: this
        });
    },
    
    /** private: method[write]
     *  :arg target: :class:`gxp.WMSStylesDialog`
     *  :arg options: ``Object``
     *
     *  Listener for the target's ``beforesaved`` event. Saves the styles of
     *  the target's ``layerRecord``. To be implemented by subclasses.
     *  Subclasses should make sure to commit changes to the target's
     *  stylesStore. It is the responsibility of the application to update
     *  displayed layers with the new style set in the target's
     *  ``selectedStyle`` record.
     */
    write: function(target, options) {
        target.stylesStore.commitChanges();
        target.fireEvent("saved", target, target.selectedStyle.get("name"));
    }

});
