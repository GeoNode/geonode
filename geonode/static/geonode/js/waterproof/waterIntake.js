async function validateCoordinateWithApi(e) {
  const snapPoint = "snapPoint";
  const delineateCatchment = "delineateCatchment";
  let center =  waterproof.cityCoords == undefined ? map.getCenter(): waterproof.cityCoords;
  let url = serverApi + snapPoint + "?x=" + center[1] + "%26y=" + center[0];
  let response = await fetch(url);
 
  let result = await response.json();
  if (result.estado) {
    let x = result.resultado.x_snap;
    let y = result.resultado.y_snap;

    if (!snapMarker) {
      snapMarker = L.marker(null, {});
      snapMarkerMapDelimit = L.marker(null, {});
    }
    var ll = new L.LatLng(y, x);
    snapMarker.setLatLng(ll);
    snapMarkerMapDelimit.setLatLng(ll);
    snapMarker.addTo(map);
    snapMarkerMapDelimit.addTo(mapDelimit);
    url = serverApi + delineateCatchment + "?x=" + x + "%26y=" + y;

    let responseCatchment = await fetch(url);
    let resultCatchment = await responseCatchment.json();
    if (resultCatchment.estado) {
      if (!catchmentPoly) {
        catchmentPoly = L.geoJSON().addTo(map);
        catchmentPolyDelimit = L.geoJSON().addTo(mapDelimit);
      } else {
        map.removeLayer(catchmentPoly);
        mapDelimit.removeLayer(catchmentPolyDelimit);
        if (editablepolygon != undefined){
          mapDelimit.removeLayer(editablepolygon);
        }
        
        catchmentPoly = L.geoJSON().addTo(map);
        catchmentPolyDelimit = L.geoJSON().addTo(mapDelimit);
      }

      catchmentPoly.addData(resultCatchment.resultado.geometry.features);
      catchmentPolyDelimit.addData(resultCatchment.resultado.geometry.features);
      basinId=resultCatchment.resultado.basin;
      map.fitBounds(catchmentPoly.getBounds());
      mapDelimit.fitBounds(catchmentPoly.getBounds());
      mapLoader.hide();
    } else {
      mapLoader.hide();
    }
  }
}
