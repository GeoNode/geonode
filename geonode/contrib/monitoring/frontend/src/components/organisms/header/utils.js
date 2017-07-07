export default (date) => {
  const today = `0${date.getDate()}`.slice(-2);
  const month = `0${date.getMonth() + 1}`.slice(-2);
  const year = date.getFullYear();
  const currentHour = `0${date.getHours()}`.slice(-2);
  const currentMinute = `0${date.getMinutes()}`.slice(-2);
  const currentSecond = `0${date.getSeconds()}`.slice(-2);
  const fromDate = `${month}/${today}/${year} ${currentHour}:${currentMinute}:${currentSecond}`;
  return fromDate;
};
