function isJson(str) {
  try {
    JSON.parse(str);
  } catch (e) {
    return false;
  }
  return true;
}

export default {
  getCookie: name => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      const cookie = parts
        .pop()
        .split(";")
        .shift();
      if (isJson(cookie)) return JSON.parse(cookie);
      return cookie;
    }
    return false;
  },
  storeCookie: (name, value) => {
    const cookie = [
      name,
      "=",
      JSON.stringify(value),
      "; domain=.",
      window.location.host.toString(),
      "; path=/;"
    ].join("");
    document.cookie = cookie;
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
