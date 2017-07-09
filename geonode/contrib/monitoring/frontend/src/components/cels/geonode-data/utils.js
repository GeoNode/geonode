const formatDate = (date) => {
  const day = `0${date.getDate()}`.slice(-2);
  const month = `0${date.getMonth() + 1}`.slice(-2);
  const year = date.getFullYear();
  const hour = `0${date.getHours()}`.slice(-2);
  const minute = `0${date.getMinutes()}`.slice(-2);
  const second = `0${date.getSeconds()}`.slice(-2);
  const formatedDate = `${year}-${month}-${day}T${hour}:${minute}:${second}`;
  return formatedDate;
};


export default formatDate;
