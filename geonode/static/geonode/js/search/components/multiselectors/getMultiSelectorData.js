import requestMultiple from "app/search/functions/requestMultiple";
import getRequestQueue from "app/search/functions/getRequestQueue";
import pyDecoder from "app/utils/pyDecoder";
import FACETS from "app/search/components/multiselectors/FACETS";

const facetsRaw = pyDecoder.decodeObject(window.djangoSearchVars.facets);
const facets = Object.entries(facetsRaw)
  .filter(facet => facet[1])
  .map(facet => ({
    id: facet[0],
    name: FACETS[facet[0]],
    count: facet[1]
  }));

export default $scope =>
  new Promise(res => {
    let requestQueue = getRequestQueue();

    // Get an array of selection data from the server
    requestMultiple(requestQueue).then(reqArray => {
      requestQueue = requestQueue.map((req, i) => {
        req.data = reqArray[i];
        $scope[requestQueue[i].id] = reqArray[i];
        return req;
      });

      // Add locally stored data to the array
      requestQueue.push({
        id: "types",
        data: facets
      });
      res(requestQueue);
    });
  });
