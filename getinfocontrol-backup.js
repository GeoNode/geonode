var getInfoCtrl = new OpenLayers.Control.WMSGetFeatureInfo({
    autoActivate: true,
    infoFormat: "application/vnd.ogc.gml",
    maxFeatures: 3,
    //url: "http://192.168.56.100:8080/geoserver/geonode/wms",
    url: geoserver,
    layers: [tile_layer],
    eventListeners: {
        "getfeatureinfo": function (e){
            var items = [];
            Ext.each (e.features, function(feature) {
                delete feature.attributes["File_Path"];
                delete feature.attributes["GRID_REF"];
                delete feature.attributes["Tilename"];
                
                items.push({
                    xtype: "propertygrid",
                    title: feature.fid,
                    source: feature.attributes
                });
            });
            
            var georef = "E"+items[0].source.MINX/1000+
                "N"+items[0].source.MAXY/1000;
            var tile_attribs = items[0].source;
            
            if (georef_list.indexOf(georef)<0){
                georef_list.push(georef);
                tile_attribs["georef"] = "feature_"+georef;
                //var visibility = highlightBox(items[0].source, highlight_layer);
                //console.log("Feature visibility is: "+ visibility)
                highlight_layer.addFeatures([e.features[0]]);
                console.log(highlight_layer.features);
                console.log(highlight_layer.drawn);
            }else{
                georef_list.splice(georef_list.indexOf(georef), 1);
                //var feature_for_removal = highlight_layer.getFeatureByFid("feature_"+georef);
                //highlight_layer.removeFeatures([feature_for_removal]);
            }
            
            console.log("Georef list after adding: "+georef_list);
            display_points("point_display");
                            
           var newpopup = new GeoExt.Popup({
                title: georef,
                width: 200,
                height: 200,
                layout: "accordion",
                map: map,
                location: e.xy,
                items: items
            });
            
            if(curr_popup != undefined){
                curr_popup.close()
            }
            curr_popup=newpopup;
            newpopup.show();
        },
        "nogetfeatureinfo": function(e){
            console.log("No queryable layer found");
        }
    }
});
