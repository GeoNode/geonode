// (object, booleanPropName) => object
export default (obj, prop) => {
  obj[prop] = !obj[prop];
  return obj;
};
