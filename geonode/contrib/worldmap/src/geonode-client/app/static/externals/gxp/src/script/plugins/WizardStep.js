/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @require plugins/Tool.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = WizardStep
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: WizardStep(config)
 *
 *    Base class for application plugins that are part of a wizard interface.
 *    To use this in an application, the outputTarget of each wizard step needs
 *    to go into the same container, with no other items in it. Also, the
 *    container needs to be configured with the
 *    :class:`gxp.plugins.WizardContainer` plugin.
 *
 *    A typical viewer with a wizard interface would have a container like
 *    this in its ``portalItems``:
 *
 *    .. code-block:: javascript
 *
 *      {
 *          layout: "accordion",
 *          width: 280,
 *          items: [{
 *              id: "step1",
 *              title: "Step 1 - do something"
 *          }, {
 *              id: "step2",
 *              title: "Step 2 - do more"
 *          }],
 *          plugins: [gxp.plugins.WizardContainer]
 *      }
 *
 *    The wizard step plugins that inherit from this base class would then be
 *    configured like this in the viewer's ``tools`` configuration:
 *
 *    .. code-block:: javascript
 *
 *      {
 *          ptype: "app_step1",
 *          outputTarget: "step1"
 *      }, {
 *          ptype: "app_stap2",
 *          outputTarget: "step2"
 *      }
 *
 *    The app_step1 plugin could look like this:
 *
 *    .. code-block:: javascript
 *
 *      app.Step1 = Ext.extend(gxp.plugins.WizardStep, {
 *
 *          // autoActivate is false by default, but for many workflows it
 *          // makes sense to start with step 1 active
 *          autoActivate: true,
 *
 *          addOutput: function(config) {
 *              return app.Step1.superclass.addOutput({
 *                  xtype: "form",
 *                  monitorValid: true,
 *                  items: [{
 *                      xtype: "textfield",
 *                      ref: "myValue",
 *                      allowBlank: false
 *                  }],
 *                  listeners: {
 *                      "clientvalidation": function(cmp, valid) {
 *                          // Set the valid state of this wizard step. If it
 *                          // is valid, the pane for step 2 will be enabled,
 *                          // and disabled otherwise.
 *                          this.setValid(valid, {step1Value: cmp.myValue})
 *                      }
 *                  }
 *              });
 *          }
 *
 *      });
 */   
gxp.plugins.WizardStep = Ext.extend(gxp.plugins.Tool, {
    
    /** api: config[autoActivate]
     *  ``Boolean`` Activate the tool as soon as the application is ready?
     *  Default is false.
     */
    autoActivate: false,
    
    /** private: property[index]
     *  ``Number`` index of this tool in the wizard container. Used for
     *  enabling and disabling step panels in sequence when another step
     *  changes its valid state. Implementations need to call the ``setValid``
     *  method to change the valid state of the wizard step.
     */
    index: null,
    
    /** private: property[valid]
     *  ``Boolean`` Is the wizard step's form currently valid?
     */
    valid: false,
    
    /** api: property[wizardContainer]
     *  ``Ext.Container`` The container that holds all wizard steps. Available
     *  after this tool's output was added to its container.
     */
    wizardContainer: null,
    
    /** api: property[wizardData]
     *  ``Object`` Merged object of all properties that wizard steps send as
     *  2nd argument of the setValid method.
     */
    wizardData: null,
    
    /** private: method[constructor]
     */
    constructor: function(config) {
        gxp.plugins.WizardStep.superclass.constructor.apply(this, arguments);
        this.wizardData = {};
    },
    
    /** private: method[addOutput]
     *  :arg config: ``Object
     */
    addOutput: function(config) {
        var output = Ext.ComponentMgr.create(Ext.apply(config, this.outputConfig));
        output.on("added",function(cmp, ct) {
            this.wizardContainer = ct.ownerCt;
            this.index = ct.ownerCt.items.indexOf(ct);
            ct.setDisabled(this.index != 0);
            ct.ownerCt.on({
                "wizardstepvalid": function(plugin, data) {
                    Ext.apply(this.wizardData, data);
                    if (this.previousStepsCompleted()) {
                        ct.enable();
                    }
                },
                "wizardstepinvalid": function(plugin) {
                    if (!this.previousStepsCompleted()) {
                        ct.disable();
                    }
                },
                scope: this
            });
            ct.on({
                "expand": this.activate,
                "collapse": this.deactivate,
                scope: this
            });
        }, this);
        return gxp.plugins.WizardStep.superclass.addOutput.call(this, output);
    },
    
    /** api: method[setValid]
     *  :arg valid: ``Boolean`` is the step's state valid?
     *  :arg data: ``Object`` data gathered by this step. Only required if
     *      ``valid`` is true.
     *
     *  Implementations should call this method to change their valid state
     */
    setValid: function(valid, data) {
        this.valid = valid;
        if (valid) {
            this.wizardContainer.fireEvent("wizardstepvalid", this, data);
        } else {
            this.wizardContainer.fireEvent("wizardstepinvalid", this);
        }
    },

    /** private: method[previousStepsCompleted]
     *  :returns: ``Boolean`` true when all previous steps are completed
     */
    previousStepsCompleted: function() {
        var index = this.index, completed = true;
        if (index > 0) {
            var tool;
            for (var i in this.target.tools) {
                tool = this.target.tools[i];
                if (tool instanceof gxp.plugins.WizardStep && tool.index < index) {
                    completed = completed && tool.valid;
                }
            }            
        }
        return completed;
    }

});
