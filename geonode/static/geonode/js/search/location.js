const svc = {
  getUrlParams() {
    const params = {};
    window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, (m, key, value) => {
      params[key] = value;
    });
    return params;
  },
  getUrlParam(param) {
    return svc.getUrlParams[param];
  }
};

export default svc;
