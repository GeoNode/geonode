Ext.namespace("GeoExplorer")


/*
 *  Create a tool to display HGL Feeds in GeoExplorer based on 1 or more keywords
 *  target: GeoExplorer instance
 */
GeoExplorer.HglFeedOverlay = function(target){
		
		this.hglRecord = null;
			
		this.popupControl = null;

        this.popup = null;
		
		this.createOverlay = function() {
			var keywords = target.about["keywords"] ? target.about["keywords"] : "of";
            var hglConfig = {name: "HGL", source: "0", group: "Overlays", buffer: "0", type: "OpenLayers.Layer.Vector",
            		args: ["HGL Points",
                    {
                        strategies: [new OpenLayers.Strategy.Fixed()],
                        protocol: new OpenLayers.Protocol.HTTP({
                                url: "/hglpoint?q=" + keywords,
                                format: new OpenLayers.Format.GeoRSS({internalProjection: new OpenLayers.Projection('EPSG:900913'),
                                    externalProjection:new OpenLayers.Projection('EPSG:4326')})
                            }),
                        displayInLayerSwitcher:false
                    }]
             };



                                                                                                                       
             var feedSource = Ext.ComponentMgr.createPlugin(
                          hglConfig, "gx_olsource"
             );
             this.hglRecord = feedSource.createLayerRecord(hglConfig);
             this.hglRecord.group = hglConfig.group;


             
     		this.popupControl = new OpenLayers.Control.SelectFeature(this.hglRecord.getLayer(), {
 			   //hover:true,
 			   clickout: true,
 			   onSelect: function(feature) {
 			      
 			      var pos = feature.geometry;
                  this.popup = new OpenLayers.Popup.FramedCloud("popup",
                             feature.geometry.getBounds().getCenterLonLat(),
                             new OpenLayers.Size(300,300),
                             "<a target='_blank' href=\"" +
 			                                         feature.attributes.link + "\">" +  feature.attributes.title +"</a><p>"+ feature.attributes.description + "</p>",
                                 //"<p><a target='_blank' href=\"javascript:onClick=app.addHGL('" +  feature.attributes.guid + "');return false;\">Display on map</a></p>",
                             null, true);
 			      this.popup.closeOnMove = false;
                  this.popup.minSize = new OpenLayers.Size(300,150);
                  this.popup.maxSize = new OpenLayers.Size(300,300);
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
    	    target.mapPanel.layers.insert(target.mapPanel.layers.data.items.length, [this.hglRecord] );
		}
		
		
		this.removeOverlay = function(){
			target.mapPanel.layers.remove(this.hglRecord, true);
			this.hglRecord = null;
			this.popupControl = null;
		}

}