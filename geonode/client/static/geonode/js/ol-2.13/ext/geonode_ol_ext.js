/**
 * @requires OpenLayers/Control.js
 * @requires OpenLayers/Control/SelectFeature.js
 * @requires OpenLayers/Handler/Keyboards.js
 * 
 * Class: OpenLayers.Control.RemoveFeature
 * Move a feature with a drag.  Create a new control with the
 *     <OpenLayers.Control.RemoveFeature> constructor.
 *
 * Inherits From:
 *  - <OpenLayers.Control>
 */
OpenLayers.Control.RemoveFeature = OpenLayers.Class(OpenLayers.Control, {

    /**
     * APIProperty: geometryTypes
     * {Array(String)} To restrict remove to a limited set of geometry types,
     *     send a list of strings corresponding to the geometry class names.
     */
    geometryTypes: null,

    /**
     * APIProperty: onDone
     * {Function} TBD add comment here
     *
     * Parameters:
     * feature - {OpenLayers.Feature.Vector} The feature that was removed.
     */
    onDone: function (feature) { },

    /**
     * Property: layer
     * {OpenLayers.Layer.Vector}
     */
    layer: null,

    /**
     * Property: feature
     * {OpenLayers.Feature.Vector}
     */
    feature: null,

    /**
     * Property: selectControl
     * {<OpenLayers.Control.Select>}
     */
    selectControl: null,

    /**
     * Constructor: OpenLayers.Control.DragFeature
     * Create a new control to drag features.
     *
     * Parameters:
     * layer - {OpenLayers.Layer.Vector} The layer containing features to be
     *     dragged.
     * options - {Object} Optional object whose properties will be set on the
     *     control.
     */
    initialize: function (layer, options) {
        OpenLayers.Control.prototype.initialize.apply(this, [options]);
        this.layer = layer;

        var control = this;
        this.selectControl = new OpenLayers.Control.SelectFeature(layer,
            {
                geometryTypes: this.geometryTypes,
                onSelect: function (feature) {
                    control.onSelect.apply(control, [feature]);
                },
                onUnselect: function (feature) {
                    control.onUnselect.apply(control, [feature]);
                }
            });
    },

    /**
     * APIMethod: destroy
     * Take care of things that are not handled in superclass
     */
    destroy: function () {
        this.layer = null;
        this.selectControl.destroy();
        OpenLayers.Control.prototype.destroy.apply(this, []);
    },

    /**
     * APIMethod: activate
     * Activate the control and the feature handler.
     * 
     * Returns:
     * {Boolean} Successfully activated the control and feature handler.
     */
    activate: function () {
        return (this.selectControl.activate() &&
            OpenLayers.Control.prototype.activate.apply(this, arguments));
    },

    /**
     * APIMethod: deactivate
     * Deactivate the control and all handlers.
     * 
     * Returns:
     * {Boolean} Successfully deactivated the control.
     */
    deactivate: function () {
        // the return from the handler is unimportant in this case
        this.selectControl.deactivate();
        return OpenLayers.Control.prototype.deactivate.apply(this, arguments);
    },

    /**
     * Method: onSelect
     * Called when the select feature control selects a feature.
     *
     * Parameters:
     * feature - {OpenLayers.Feature.Vector} The selected feature.
     */
    onSelect: function (feature) {
        this.feature = feature;
        this.remove(this.feature);
    },

    /**
     * Method: onUnselect
     * Called when the select feature control unselects a feature.
     *
     * Parameters:
     * feature - {OpenLayers.Feature.Vector} The unselected feature.
     */
    onUnselect: function (feature) {
        this.feature = null;
    },

    /**
     * Method: remove
     * Removes currently selected feature
     *
     * Parameters:
     * code - {Integer} 
     */
    remove: function (feature) {
        this.layer.removeFeatures([feature]);
        this.onDone(feature);
    },

    /**
     * Method: setMap
     * Set the map property for the control and all handlers.
     *
     * Parameters: 
     * map - {OpenLayers.Map} The control's map.
     */
    setMap: function (map) {
        this.selectControl.setMap(map);
        OpenLayers.Control.prototype.setMap.apply(this, arguments);
    },

    CLASS_NAME: "OpenLayers.Control.RemoveFeature"
});

/**
 * @requires OpenLayers/Control/Panel.js
 * @requires OpenLayers/Control/Navigation.js
 * @requires OpenLayers/Control/DrawFeature.js
 * @requires OpenLayers/Handler/Point.js
 * @requires OpenLayers/Handler/Path.js
 * @requires OpenLayers/Handler/Polygon.js
 */

/**
 * Class: OpenLayers.Control.EditingToolbar 
 * The EditingToolbar is a panel of 4 controls to draw polygons, lines, 
 * points, or to navigate the map by panning. By default it appears in the 
 * upper right corner of the map.
 * 
 * Inherits from:
 *  - <OpenLayers.Control.Panel>
 */
OpenLayers.Control.EditingToolbar = OpenLayers.Class(
    OpenLayers.Control.Panel, {

    /**
     * APIProperty: citeCompliant
     * {Boolean} If set to true, coordinates of features drawn in a map extent
     * crossing the date line won't exceed the world bounds. Default is false.
     */
    citeCompliant: false,

    /**
     * Constructor: OpenLayers.Control.EditingToolbar
     * Create an editing toolbar for a given layer. 
     *
     * Parameters:
     * layer - {<OpenLayers.Layer.Vector>} 
     * options - {Object} 
     */
    initialize: function (layer, options) {
        OpenLayers.Control.Panel.prototype.initialize.apply(this, [options]);

        this.addControls(
          [ new OpenLayers.Control.Navigation() ]
        );
        var controls = [
            /*new OpenLayers.Control.DrawFeature(layer, OpenLayers.Handler.Point, {
                displayClass: 'olControlDrawFeaturePoint',
                handlerOptions: {citeCompliant: this.citeCompliant}
            }),
            new OpenLayers.Control.DrawFeature(layer, OpenLayers.Handler.Path, {
                displayClass: 'olControlDrawFeaturePath',
                handlerOptions: {citeCompliant: this.citeCompliant}
            }),*/
            new OpenLayers.Control.RemoveFeature(layer, {
                displayClass: 'olControlRemoveFeature'
            }),
            new OpenLayers.Control.DrawFeature(layer, OpenLayers.Handler.Polygon, {
                displayClass: 'olControlDrawFeaturePolygon',
                handlerOptions: { citeCompliant: this.citeCompliant }
            })
        ];
        this.addControls(controls);
    },

    /**
     * Method: draw
     * calls the default draw, and then activates mouse defaults.
     *
     * Returns:
     * {DOMElement}
     */
    draw: function () {
        var div = OpenLayers.Control.Panel.prototype.draw.apply(this, arguments);
        if (this.defaultControl === null) {
            this.defaultControl = this.controls[0];
        }
        return div;
    },

    CLASS_NAME: "OpenLayers.Control.EditingToolbar"
});