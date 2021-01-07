async function validateCoordinateWithApi(e) {
  const snapPoint = "snapPoint";
  const delineateCatchment = "delineateCatchment";
  let center = map.getCenter();
  let url = serverApi + snapPoint + "?x=" + center.lng + "&y=" + center.lat;
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
    url = serverApi + delineateCatchment + "?x=" + x + "&y=" + y;

    let responseCatchment = await fetch(url);
    let resultCatchment = await responseCatchment.json();
    if (resultCatchment.estado) {
      if (!catchmentPoly) {
        catchmentPoly = L.geoJSON().addTo(map);
        catchmentPolyDelimit = L.geoJSON().addTo(mapDelimit);
      } else {
        map.removeLayer(catchmentPoly);
        catchmentPoly = L.geoJSON().addTo(map);
        catchmentPolyDelimit = L.geoJSON().addTo(mapDelimit);
      }

      catchmentPoly.addData(resultCatchment.resultado.features);
      catchmentPolyDelimit.addData(resultCatchment.resultado.features);
      map.fitBounds(catchmentPoly.getBounds());
      mapDelimit.fitBounds(catchmentPoly.getBounds());
      mapLoader.hide();
    } else {
      mapLoader.hide();
    }
  }
}
