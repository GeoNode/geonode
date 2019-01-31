/*
  Build a url query string based on an object and add it to
  the request endpoint.
*/

export default (url, params) =>
  new Promise(res => {
    const esc = encodeURIComponent;
    const query = Object.keys(params)
      .map(k => `${esc(k)}=${esc(params[k])}`)
      .join("&");
    fetch(`${url}?${query}`)
      .then(r => r.json())
      .then(data => {
        res(data);
      });
  });
