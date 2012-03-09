Ext.namespace("GeoExplorer")


/*
 *  Create a tool to display Picasa Feeds in GeoExplorer based on 1 or more keywords
 *  target: GeoExplorer instance
 */
GeoExplorer.PicasaFeedOverlay = function(target){
		
		this.picasaRecord = null;
			
		this.popupControl = null;

        this.popup = null;
		
		this.createOverlay = function() {
			var keywords = target.about["keywords"] ? target.about["keywords"] : "of";
            var picasaConfig = {name: "Picasa", source: "0", group: "Overlays", buffer: "0", type: "OpenLayers.Layer.WFS",  
            		args: ["Picasa Pictures", "/picasa/", 
                           { 'kind': 'photo', 'max-results':'50', 'q' : keywords},
                           {  format: OpenLayers.Format.GeoRSS, projection: "EPSG:4326", displayInLayerSwitcher: false, 
                              formatOptions: {
                                              createFeatureFromItem: function(item) {
                                                                     var feature = OpenLayers.Format.GeoRSS.prototype
                                                                                   .createFeatureFromItem.apply(this, arguments);
                                                                                    feature.attributes.thumbnail = this.getElementsByTagNameNS(item, "http://search.yahoo.com/mrss/", "thumbnail")[0].getAttribute("url");
                                                                                    feature.attributes.content = OpenLayers.Util.getXmlNodeValue(this.getElementsByTagNameNS(item, "*","summary")[0]);
                                                                                    return feature;
                                                                                    }
                                             },
                              styleMap: new OpenLayers.StyleMap({
                                                                 "default": new OpenLayers.Style({externalGraphic: "${thumbnail}", pointRadius: 14}),
                                                                 "select": new OpenLayers.Style({pointRadius: 20})
                                                               })
                      }]
             };

            
            
                                                                                                                       
             var feedSource = Ext.ComponentMgr.createPlugin(
                          picasaConfig, "gx_olsource"
             );
             this.picasaRecord = feedSource.createLayerRecord(picasaConfig);
             this.picasaRecord.group = picasaConfig.group;
             
             
     		this.popupControl = new OpenLayers.Control.SelectFeature(this.picasaRecord.getLayer(), {
 			   //hover:true,
 			   clickout: true,
 			   onSelect: function(feature) {
 			      
 			      var pos = feature.geometry;
                  var content = document.createElement("div");
                  content.innerHTML = feature.attributes.content;
 			      this.popup = new OpenLayers.Popup("popup",
 			                                         new OpenLayers.LonLat(pos.x, pos.y),
 			                                         new OpenLayers.Size(160,160),
 			                                         "<a target='_blank' href=" + 
 			                                         content.getElementsByTagName('a')[0].getAttribute('href') +"><img title='" +
 			                                         feature.attributes.title +"' src='" + feature.attributes.thumbnail +"' /></a>",
 			                                         false);
 			      this.popup.closeOnMove = true;
 			      this.popup.keepInMap = true;
 			      target.mapPanel.map.addPopup(this.popup);
 	        },
 	        
 	        onUnselect: function(feature) {
 	        	target.mapPanel.map.removePopup(this.popup);
 	            this.popup = null;
 	        }
 	       }); 
             
    		target.mapPanel.map.addControl(this.popupControl);
    	    this.popupControl.activate();
    	    target.mapPanel.layers.insert(target.mapPanel.layers.data.items.length, [this.picasaRecord] );
		}
		
		
		this.removeOverlay = function(){
			target.mapPanel.layers.remove(this.picasaRecord, true);
			this.picasaRecord = null;
			this.popupControl = null;
		}

}