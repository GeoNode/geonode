
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: SearchBar(target)
 */   
gxp.SearchBar =  function(target) {
    
		this.target = target;
		
		var getQueryableLayers = function() {
			    return target.mapPanel.layers.queryBy(function(x){
                return x.get("queryable");
            });
		};
		
		
//		var searchLayerStore = function() {
//			var ql = getQueryableLayers();
//			var ls = [];
//            ql.each(function(x){
//            	alert(x.title);
//            	dl = x.getLayer();
//            	ls.push(x);
//            });
//			return ls;
//		}
		
        var searchTB = new Ext.form.TextField({
			id:'search-tb',
			width:150,
			emptyText:'Enter search...'
		});
        
        var psHandler = function() {
        	performSearch.call();
        	};
        
        var searchBtn = new Ext.Button({
			text:'<span class="x-btn-text">Search</span>',
			handler: psHandler
		});
        
		
//		var slReader = new Ext.data.ArrayReader({}, searchLayerStore); 
//
//		var slProxy = new Ext.data.MemoryProxy(slReader);
//		
//		 var slStore = new Ext.data.Store({                                    
//     		reader : slReader,
//     		autoLoad: true,
//     		proxy  : slProxy
// 		});
//		
//		var searchLayerCombo = new Ext.form.ComboBox({
//    		store:slStore,
//    		displayField:'title',
//    		emptyText:'Select a search layer',
//    		selectOnFocus:true
//		});
//
//		
//		var updateSearchLayers = function() {
//			searchLayerCombo.store.reload();
//		}
		
    	var performSearch =  function() {

    		// Find queryable layers (visible with searchable fields)
    		var searchCount = 0;
            var queryableLayers = getQueryableLayers();
            queryableLayers.each(function(x){
            	dl = x.getLayer();
            	if (!dl.getVisibility() || dataLayers[dl.params.LAYERS].count == 0)
            		{queryableLayers.remove(x, true);}
            });
            if (queryableLayers.length == 0)
            	{
                Ext.MessageBox.alert('No Searchable Layers','There are currently no searchable layers on the map.  You must have at least one visible layer with searchable fields on the map.');
                return;
            	
            	}
    		
            //show searching modal
            if (!target.busyMask) {
                target.busyMask = new Ext.LoadMask(
                    target.mapPanel.map.div, {
                        msg: 'Searching...'
                    }
                );
            }
            target.busyMask.show();
    		
            try{
            //Get rid of any existing highlight layers
            removeHighlightLayers();
            
            //search term manipulation code, copied verbatim from existing WorldMap
    		searchTerm = searchTB.getValue();
            var terms = [];
            var matchingSearchTerm = searchTerm;
            var re = /("[^"]+")/g;
            var m = matchingSearchTerm.match(re);
            var otherSearchTerm = searchTerm; 
            if ( m != null ) {
                for ( i = 0; i < m.length; i++ ) {
                    otherSearchTerm = otherSearchTerm.replace(m[i], '');
                    terms.push( m[i].replace(/"/g, '' ));
                }	
            } else {
            }          
            var whitespace_re = /\s+/;
            otherSearchTerm = otherSearchTerm.replace(whitespace_re, ' ');
            terms = terms.concat(otherSearchTerm.split(' '));
            layers = [];
            
            //Create a WMS search results layer for each searchable layer
            queryableLayers.each(function(x){
            	dl = x.getLayer();
            	if (dl.getVisibility())
            		{
            		
            		var wms_url = dl.url;
            			queryFields = [];
            			for (f=0; f < dataLayers[dl.params.LAYERS].searchFields.length; f++)
            			{
            				field = dataLayers[dl.params.LAYERS].searchFields[f]
            				
            				if (field.searchable == "True") {
            					queryFields.push(field.attribute);
            				}
            			}
            			
            			
            			featureQuery="";
            			
            			sld = '';//'<?xml version="1.0" encoding="utf-8"?>';
            			sld+= '<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0">';
            			sld+= '<sld:NamedLayer><sld:Name>' + dl.params.LAYERS  +  '</sld:Name><sld:UserStyle><sld:Name>query</sld:Name><sld:FeatureTypeStyle><sld:Rule><ogc:Filter>';
            			for (i = 0; i < queryFields.length; i++)
            				{
            					if (queryFields[i] != "")
            						featureQuery = featureQuery + '<ogc:PropertyIsLike wildCard="*" singleChar="." escapeChar="!"><ogc:PropertyName>' + queryFields[i] + '</ogc:PropertyName><ogc:Literal>*' + searchTerm + '*</ogc:Literal></ogc:PropertyIsLike>';
            				}
            			if (queryFields.length > 1)
            				{
            					featureQuery = "<ogc:Or>"+ featureQuery + "</ogc:Or>";	
            				}
            			if (featureQuery.length > 0)
            				{            				
        					sld += featureQuery;
        					sld += '</ogc:Filter>';
        					
        				    //Points        					
        					sld += '<PointSymbolizer><Graphic><Mark><WellKnownName>circle</WellKnownName><Fill><CssParameter name="fill">#FFFF00</CssParameter></Fill></Mark><Size>8</Size></Graphic></PointSymbolizer>';
        					//Lines
        					sld += '<LineSymbolizer><sld:Stroke><sld:CssParameter name="stroke">#FFFF00</sld:CssParameter><sld:CssParameter name="stroke-opacity">1.0</sld:CssParameter><sld:CssParameter name="stroke-width">2</sld:CssParameter></sld:Stroke></LineSymbolizer>';
        					//Polygons
        					//sld += '<sld:PolygonSymbolizer> <sld:Fill><sld:GraphicFill> <sld:Graphic><sld:Mark> <sld:WellKnownName>shape://times</sld:WellKnownName> <sld:Stroke><sld:CssParameter name="stroke">#FFFF00</sld:CssParameter>';
        					//sld += '<sld:CssParameter name="stroke-width">1</sld:CssParameter> </sld:Stroke></sld:Mark><sld:Size>16</sld:Size> </sld:Graphic></sld:GraphicFill> </sld:Fill></sld:PolygonSymbolizer>';        					     					
        					sld += '</sld:Rule></sld:FeatureTypeStyle></sld:UserStyle></sld:NamedLayer></sld:StyledLayerDescriptor>';        					 
        					 
        					
                    		wmsHighlight = new OpenLayers.Layer.WMS(
            						"HighlightWMS",
            						wms_url,
            						{'layers': dl.params.LAYERS,'format':'image/png', SLD_BODY: sld, TRANSPARENT: 'true'},
            						{'isBaseLayer': false,'displayInLayerSwitcher' : false}
                    		);
                    		layers.push(wmsHighlight);
        					
            				}
            		}
            });
            
            target.mapPanel.map.addLayers(layers);  
            } catch (e) {
            	//Suppress for now
            } finally {
        		if (target.busyMask) {
        			target.busyMask.hide();
        		}
            }
            

    	};
    	
    	var reset =  function() { 
    		searchTB.setValue('');
            removeHighlightLayers();

    	};
    	        
        var removeHighlightLayers  = function() {
        	var theLayers = target.mapPanel.map.layers;
        	var hLayers = [];
            for (l = 0; l < theLayers.length; l++)
        	{
        		if (theLayers[l].name == "HighlightWMS" || theLayers[l].name == "hilites"){
        			hLayers.push(theLayers[l]);
        			
        		} 
        		
        	}
            
            for (h = 0; h < hLayers.length; h++)
            	{
            		target.mapPanel.map.removeLayer(hLayers[h],true);
            	}
            
        }
        
		var searchBar = new Ext.Toolbar({
			id: 'tlbr',
			items:[searchTB,
				' ', searchBtn,' ',{
					xtype:'button',
					text:'<span class="x-btn-text">Reset</span>',
					handler:function(brn, e) {
						reset();
					}
				}]
		});
		
		return searchBar;
    	
    }
