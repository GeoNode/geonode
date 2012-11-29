/**
 * Copyright (c) 2008 The Open Planning Project
 */

Ext.namespace("Styler");

/**
 * Class: Styler.ColorManager
 * A simple manager that handles the rendering of a ColorPicker window and
 *     coordinates the setting of values in a ColorField.  May be used as a
 *     plugin for a ColorField (or any text field that is intended to gather a
 *     RGB hex color value).
 */
Styler.ColorManager = function(config) {
    Ext.apply(this, config);
};

Ext.apply(Styler.ColorManager.prototype, {
    
    /**
     * Property: field
     * {<Styer.form.ColorField>} The currently focussed field.
     */
    field: null,
    
    /**
     * Method: init
     * Called when the color manager is used as a plugin.
     *
     * Parameters:
     * field - {<Styler.form.ColorField>} The field using this manager as a
     *     plugin.
     */
    init: function(field) {
        this.register(field);
    },
    
    /**
     * Method: destroy
     * Cleans up the manager.
     */
    destroy: function() {
        if(this.field) {
            this.unregister(this.field);
        }
    },
    
    
    /**
     * Method: register
     * Register a field with this manager.
     *
     * Parameters:
     * field - {<Styler.form.ColorField>} The field using this manager as a
     *     plugin.
     */
    register: function(field) {
        if(this.field) {
            this.unregister(this.field);
        }
        this.field = field;
        field.on({
            focus: this.fieldFocus,
            destroy: this.destroy,
            scope: this
        });
    },
    
    /**
     * Method: unregister
     * Unregister a field with this manager.
     * 
     * Parameters:
     * field - {<Styler.form.ColorField>} The field using this manager as a
     *     plugin.
     */
    unregister: function(field) {
        field.un("focus", this.fieldFocus, this);
        field.un("destroy", this.destroy, this);
        if(Styler.ColorManager.picker && field == this.field) {
            Styler.ColorManager.picker.un("pickcolor", this.setFieldValue, this);
        }
        this.field = null;
    },
    
    /**
     * Method: fieldFocus
     * Listener for "focus" event on a field.
     *
     * Parameters:
     * field - {<Styler.form.ColorField>} The focussed field.
     */
    fieldFocus: function(field) {
        if(!Styler.ColorManager.pickerWin) {
            Styler.ColorManager.picker = new Ext.ux.ColorPanel({
                hidePanel: false,
                autoHeight: false
            });
            Styler.ColorManager.pickerWin = new Ext.Window({
                title: "Color Picker",
                layout: "fit",
                closeAction: "hide",
                width: 405,
                height: 300,
                plain: true,
                items: Styler.ColorManager.picker
            });
        }
        Styler.ColorManager.picker.purgeListeners();
        this.setPickerValue();
        Styler.ColorManager.picker.on({
            pickcolor: this.setFieldValue,
            scope: this
        });
        Styler.ColorManager.pickerWin.show();
    },
    
    /**
     * Method: setFieldValue
     * Listener for the "pickcolor" event of the color picker.  Only sets the
     *     field value if the field is visible.
     *
     * Parameters:
     * picker - {Ext.ux.ColorPicker} The color picker
     * color - {String} The RGB hex value (not prefixed with "#")
     */
    setFieldValue: function(picker, color) {
        if(this.field.isVisible()) {
            this.field.setValue("#" + color);
        }
    },
    
    /**
     * Method: setPickerValue
     */
    setPickerValue: function() {
        var field = this.field;
        var hex = field.getHexValue ? field.getHexValue() : field.getValue();
        if(hex) {
            Styler.ColorManager.picker.setColor(hex.substring(1));
        }
    }
    
});

Styler.ColorManager.picker = null;

Styler.ColorManager.pickerWin = null;