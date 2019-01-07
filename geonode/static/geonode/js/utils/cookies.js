export default {
  getCookie: name => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2)
      return parts
        .pop()
        .split(";")
        .shift();
    return false;
  },
  getAll: () => {
    const pairs = document.cookie.split(";");
    const cookies = {};
    for (let i = 0; i < pairs.length; i++) {
      const pair = pairs[i].split("=");
      cookies[`${pair[0]}`.trim()] = unescape(pair[1]);
    }
    return cookies;
  },
  remove(name) {
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:01 GMT;`;
  }
};
