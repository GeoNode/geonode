// getNewMapURL :: (String, Array) -> String
export default (siteUrl, layers) => {
  let params = "";
  if (layers) {
    for (let i = 0; i < layers; i++) {
      params += `layer=${layers[i]}&`;
    }
  }
  return `${siteUrl}maps/new?${params}`;
};
