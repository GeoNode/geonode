/**
 * Class: OpenLayers.FeatureAgent
 * An agent that manages feature related events.
 */
OpenLayers.LayerFeatureAgent = OpenLayers.Class({
    
    /**
     * Property: cache
     * {Object} A cache of features under the mouse.
     */
    cache: null,
    
    /**
     * Constructor: OpenLayers.FeatureAgent
     * Create a new feature agent.
     *
     * Parameters:
     * map - {<OpenLayers.Map>} The map with vector layers.
     * options - {Object} Optional object with properties to be set on the agent.
     */
    initialize: function(layer, options) {
        OpenLayers.Util.extend(this, options);
        this.options = options;
        this.layer = layer;
    },
    
    /** 
     * APIMethod: activate
     * Activate the agent.
     */
    activate: function() {
    	if (!this.activated) {
    		this.cache = {};
    		this.activated = true;
    		this.layer.events.on({
    			click: this.onClick,
    			scope: this
    		});
    	}
    },
    
    /** 
     * APIMethod: deactivate
     * Deactivate the agent.
     */
    deactivate: function() {
    	if (this.activated) {
    		this.activated = false;
    		this.cache = {};
        	this.layer.events.un({
            	click: this.onClick,
            	scope: this
        	});  
    	}
    },
    
    /**
     * Method: onClick
     * Listener for the click event.
     *
     * Parameters:
     * evt - {<OpenLayers.Event>}
     */
    onClick: function(evt) {
        var features = this.getFeatures(evt.clientX, evt.clientY);
        if (features.length > 1) {
        	this.layer.events.triggerEvent(
                    "multipleselected", {features: features});
        } else {
        	// fire featureclick events
        	var feature, more, clicked = {};
        	for (i=0, len=features.length; i<len; ++i) {
        		feature = features[i];
        		//layer = feature.layer;
        		clicked[this.layer.id] = true;
        		more = this.layer.events.triggerEvent(
        				"featureselected", {feature: feature}
        		);
        		if (more === false) {
        			break;
        		}
        	}
        }
    },

 
    /**
     * Method: getFeatures
     * Get all features at the given screen location.
     *
     * Parameters:
     * x - {Number} Screen x coordinate.
     * y - {Number} Screen y coordinate.
     *
     * Returns:
     * {Array(<OpenLayers.Feature.Vector>)} List of features at the given point.
     */
    getFeatures: function(x, y) {
        var features = [], targets = [], layers = [];
        var layer, target, feature, i, len;
        // go through all layers looking for targets
        //do (i=this.map.layers.length-1; i>=0; --i) {
            layer = this.layer; //this.map.layers[i];
            if (layer.div.style.display !== "none") {
                if (layer instanceof OpenLayers.Layer.Vector) {
                    target = document.elementFromPoint(x, y);
                    while (target && (target._featureId || target.nearestViewportElement)) {
                        feature = target._featureId ? layer.getFeatureById(target._featureId):
                        	layer.getFeatureById(target.nearestViewportElement._featureId);
                        if (feature) {
                            features.push(feature);
                        }
                        target.style.display = "none";
                        targets.push(target);
                        target = document.elementFromPoint(x, y);
                    }
                }
                layers.push(layer);
                layer.div.style.display = "none";
            }
        //}
        // restore feature visibility
        for (i=0, len=targets.length; i<len; ++i) {
            targets[i].style.display = "";
        }
        // restore layer visibility
        for (i=layers.length-1; i>=0; --i) {
            layers[i].div.style.display = "block";
        }
        return features;
    },
    
    /**
     * APIMethod: destroy
     * Clean up.
     */
    destroy: function() {
        this.deactivate();
        delete this.cache;
        delete this.layer;
    },
    
    /**
     * Method: highlight
     * Redraw feature with the select style.
     *
     * Parameters:
     * feature - {<OpenLayers.Feature.Vector>} 
     */
    highlight: function(feature) {

            feature._prevHighlighter = feature._lastHighlighter;
            feature._lastHighlighter = this.id;
            var style = this.selectStyle || this.renderIntent;
            this.layer.drawFeature(feature, style);
        
    },

    /**
     * Method: unhighlight
     * Redraw feature with the "default" style
     *
     * Parameters:
     * feature - {<OpenLayers.Feature.Vector>} 
     */
    unhighlight: function(feature) {
        var layer = feature.layer;
        // three cases:
        // 1. there's no other highlighter, in that case _prev is undefined,
        //    and we just need to undef _last
        // 2. another control highlighted the feature after we did it, in
        //    that case _last references this other control, and we just
        //    need to undef _prev
        // 3. another control highlighted the feature before we did it, in
        //    that case _prev references this other control, and we need to
        //    set _last to _prev and undef _prev
        if(feature._prevHighlighter == undefined) {
            delete feature._lastHighlighter;
        } else if(feature._prevHighlighter == this.id) {
            delete feature._prevHighlighter;
        } else {
            feature._lastHighlighter = feature._prevHighlighter;
            delete feature._prevHighlighter;
        }
        this.layer.drawFeature(feature, feature.style || this.layer.style ||
            "default");
    },    
    
    
    CLASS_NAME: "OpenLayers.LayerFeatureAgent"
    
});