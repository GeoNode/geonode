// (styleObject, boolean) => styleObject;
export default (bool, styleObject = {}) => {
  if (bool) styleObject.display = "none";
  else styleObject.display = "block";
  return styleObject;
};
