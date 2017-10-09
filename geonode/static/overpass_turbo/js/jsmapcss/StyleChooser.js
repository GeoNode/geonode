// styleparser/StyleChooser.js

styleparser.StyleChooser = function() {
    this.ruleChains = [new styleparser.RuleChain()];
    this.styles = [];
};

styleparser.StyleChooser.prototype = {
	// UpdateStyles doesn't support image-widths yet
	// or setting maxwidth/_width
	ruleChains: [],				// array of RuleChains (each one an array of Rules)
	styles: [],					// array of ShapeStyle/ShieldStyle/TextStyle/PointStyle
	zoomSpecific:false,			// are any of the rules zoom-specific?

	rcpos:0,
	stylepos:0,

	constructor:function() {
		// summary:		A combination of the selectors (ruleChains) and declaration (styles).
		//				For example, way[highway=footway] node[barrier=gate] { icon: gate.png; } is one StyleChooser.
	},

	currentChain:function() {
		return this.ruleChains[this.ruleChains.length-1];
	},

	newRuleChain:function() {
		// summary:		Starts a new ruleChain in this.ruleChains.
		if (this.ruleChains[this.ruleChains.length-1].length()>0) {
			this.ruleChains.push(new styleparser.RuleChain());
		}
	},

	addStyles:function(a) {
		this.styles=this.styles.concat(a);
	},

	updateStyles:function(entity, tags, sl, zoom) {
		if (this.zoomSpecific) { sl.validAt=zoom; }

		// Are any of the ruleChains fulfilled?
		var w;
		for (var i in this.ruleChains) {
			var c=this.ruleChains[i];
			if (c.test(-1, entity, tags, zoom)) {
				sl.addSubpart(c.subpart);

				// Update StyleList
				for (var j in this.styles) {
					var r=this.styles[j];
					var a;
					switch (r.styleType) {

						case 'ShapeStyle' :	sl.maxwidth=Math.max(sl.maxwidth,r.maxwidth());
											a=sl.shapeStyles; break;
						case 'ShieldStyle':	a=sl.shieldStyles; break;
						case 'TextStyle'  :	a=sl.textStyles; break;
						case 'PointStyle' :	sl.maxwidth=Math.max(sl.maxwidth,r.maxwidth());
											a=sl.pointStyles; break;
						case 'InstructionStyle':
						    if (r.breaker) { return; }
							for (var k in r.set_tags) { tags[k]=r.set_tags[k]; }
							a = {}; // "dev/null" stylechooser reciever
							break;
					}
					if (r.drawn()) { tags[':drawn']='yes'; }
					tags._width = sl.maxwidth;
			
					r.runEvals(tags);
                                        // helper function
                                        function extend(destination, source) {
                                          for (var property in source) {
                                            if (source.hasOwnProperty(property)) {
                                              destination[property] = source[property];
                                            }
                                          }
                                          return destination;
                                        };
					if (a[c.subpart]) {
						// // If there's already a style on this sublayer, then merge them
						// // (making a deep copy if necessary to avoid altering the root style)
						// if (!a[c.subpart].merged) { a[c.subpart]=extend({},a[c.subpart]); }
						extend(a[c.subpart], r);
					} else {
						// // Otherwise, just assign it
						a[c.subpart]=extend({},r);
					}
				}
			}
		}
	}
};
