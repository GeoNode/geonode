const svc = {
  getUrlParams() {
    const params = {};
    window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, (m, key, value) => {
      params[key] = value;
    });
    return params;
  },
  getUrlParam(param) {
    return svc.getUrlParams()[param];
  },
  paramExists(param) {
    return (
      svc.getUrlParams()[param] !== null &&
      svc.getUrlParams()[param] !== undefined
    );
  }
};

export default svc;
