// getCartSession :: Object => [Object]
export default cookies => {
  const geonodeCart = cookies;
  const cartSession = [];
  if (geonodeCart !== null) {
    if (Object.keys(geonodeCart).length > 1) {
      Object.keys(geonodeCart).forEach((key, index) => {
        if (key !== "csrftoken") {
          try {
            const obj = JSON.parse(geonodeCart[key]);
            obj["$$hashKey"] = `object:${index}`;
            if ("alternate" in obj) {
              cartSession.push(obj);
            }
          } catch (err) {
            // eslint-disable-next-line
            console.log("Cart Session Issue: " + err.message);
          }
        }
      });
    }
  }
  return cartSession;
};
