/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = WizardContainer
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: WizardContainer(config)
 *
 *    Static plugin for adding wizard step validation management to containers
 *    that hold the output from :class:`gxp.plugins.WizardStep`
 *    implementations. Events shown here are fired by the container that is
 *    extended with this plugin.
 *
 *    Detailed instructions on how to work with wizard containers and wizard
 *    step plugins can be found in the :class:`gxp.plugins.WizardStep`
 *    documentation.
 */   
gxp.plugins.WizardContainer = {

    /** private: method[init]
     *  :arg target: ``Object
     */
    init: function(target) {
        target.addEvents(
            /** private: event[wizardstepvalid]
             *  Triggered when a wizard step is valid.
             *
             *  Listener arguments:
             *
             *  * ``gxp.plugins.Tool`` - the wizard step plugin
             *  * ``Object`` - data gathered by this wizard step
             */
            "wizardstepvalid",
            
            /** private: event[wizardstepinvalid]
             *  Triggered when a wizard step is invalid.
             *
             *  Listener arguments:
             *
             *  * ``gxp.plugins.Tool`` - the wizard step plugin
             */
            "wizardstepinvalid",
            
            /** api: event[wizardstepexpanded]
             *  Triggered when a wizard step is expanded.
             *
             *  Listener arguments:
             *
             *  * ``Number`` - the index of the expanded wizard step
             */
            "wizardstepexpanded"
        );
        
        target.on("add", function(cmp) {
            cmp.on("expand", function() {
                target.fireEvent("wizardstepexpanded", target.items.indexOf(cmp));
            });
        });
    }

};

Ext.preg("gxp_wizardcontainer", gxp.plugins.WizardContainer);
