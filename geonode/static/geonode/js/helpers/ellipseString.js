import functional from "app/utils/functional";

// (number) => (string) => string
export default functional.curry((ln, str) => {
  if (!str) return "";
  let newStr = "";
  newStr += str.slice(0, ln);
  if (str.length > ln) return `${newStr}...`;
  return newStr;
});
