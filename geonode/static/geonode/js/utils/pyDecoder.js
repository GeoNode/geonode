export default {
  decodeObject: string => {
    const decoded = $("<textarea/>")
      .html(string)
      .text();
    return JSON.parse(decoded.replace(/'/g, '"'));
  }
};
