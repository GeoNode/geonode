

async function validateCoordinateWithApi(e){
    const snapPoint = "snapPoint";
    const delineateCatchment = "delineateCatchment";
    let center = map.getCenter();    
    let url = serverApi + snapPoint + "?x=" + center.lng + "&y=" + center.lat;
    let response = await fetch(url);
    mapLoader = L.control.loader().addTo(map);
    let result = await response.json();
    if (result.estado){
      let x = result.resultado.x_snap;
      let y = result.resultado.y_snap;
      
      if (!snapMarker){
        snapMarker = L.marker(null, {});        
      }
      var ll = new L.LatLng(y, x);
			snapMarker.setLatLng(ll);
      snapMarker.addTo(map);
      
      url = serverApi + delineateCatchment + "?x=" + x + "&y=" + y;

      let responseCatchment = await fetch(url);
      let resultCatchment = await responseCatchment.json();
      if (resultCatchment.estado){
        if (!catchmentPoly){
          catchmentPoly = L.geoJSON().addTo(map);
        }else{
          map.removeLayer(catchmentPoly);
          catchmentPoly = L.geoJSON().addTo(map);
        }
        
        catchmentPoly.addData(resultCatchment.resultado.features);
        map.fitBounds(catchmentPoly.getBounds());
        mapLoader.hide();   
      }else{
        mapLoader.hide(); 
      }
    }
  }
  