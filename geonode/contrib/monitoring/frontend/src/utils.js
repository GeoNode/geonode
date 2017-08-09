import isomorphicFetch from 'isomorphic-fetch';
import { minute, hour, day, week } from './constants';


export const fetch = (args) => {
  const {
    url,
    body,
    method,
  } = args;
  const newbody = JSON.stringify(body);
  const newargs = {
    body: newbody,
    method: method || 'GET',
    headers: { Accept: 'application/json' },
  };
  if (method === 'POST' || method === 'PUT' || method === 'PATCH') {
    newargs.headers['Content-Type'] = 'application/json';
  }
  return isomorphicFetch(url, newargs)
    .then(response => {
      const json = response.json();
      if (response.status >= 400) {
        const error = new Error(response.statusText);
        error.response = response;
        throw error;
      }
      return json;
    });
};


export const formatApiDate = (date) => {
  const theday = `0${date.getDate()}`.slice(-2);
  const themonth = `0${date.getMonth() + 1}`.slice(-2);
  const theyear = date.getFullYear();
  const thehour = `0${date.getHours()}`.slice(-2);
  const theminute = `0${date.getMinutes()}`.slice(-2);
  const thesecond = `0${date.getSeconds()}`.slice(-2);
  return `${theyear}-${themonth}-${theday}%20${thehour}:${theminute}:${thesecond}`;
};


export const formatHeaderDate = (date) => {
  const theday = `0${date.getDate()}`.slice(-2);
  const themonth = `0${date.getMonth() + 1}`.slice(-2);
  const theyear = date.getFullYear();
  const thehour = `0${date.getHours()}`.slice(-2);
  const theminute = `0${date.getMinutes()}`.slice(-2);
  const thesecond = `0${date.getSeconds()}`.slice(-2);
  return `${themonth}/${theday}/${theyear} ${thehour}:${theminute}:${thesecond}`;
};


export const sequenceInterval = (getState) => {
  const interval = getState().interval.interval;
  let seqInterval = interval;
  if (interval === 10 * minute) {
    seqInterval = minute;
  } else if (interval === hour) {
    seqInterval = 5 * minute;
  } else if (interval === day) {
    seqInterval = 2 * hour;
  } else if (interval === week) {
    seqInterval = 12 * hour;
  }
  return seqInterval;
};


export const getResponseData = (response) => {
  let averageResponseTime;
  let maxResponseTime;
  let totalRequests;
  if (!response || !response.data) {
    return [averageResponseTime, maxResponseTime, totalRequests];
  }
  const rawData = response.data.data;
  const rawDataLength = rawData.length;
  if (rawDataLength > 0) {
    let dataIndex = rawDataLength - 1;
    let data = rawData[dataIndex];
    if (!data.data || data.data.length === 0) {
      if (rawDataLength > 1) {
        --dataIndex;
      }
      data = rawData[dataIndex];
    }
    const dataLength = data.data.length;
    if (dataLength > 0) {
      const metric = data.data[dataLength - 1];
      maxResponseTime = Math.floor(metric.max);
      averageResponseTime = Math.floor(metric.val);
      totalRequests = metric.samples_count;
    }
  }
  return [averageResponseTime, maxResponseTime, totalRequests];
};


export const getCount = (responses) => {
  let result = [];
  if (!responses || !responses.data || !responses.data.data) {
    return result;
  }
  result = responses.data.data.map(element => ({
    name: element.valid_from,
    count: element.data.length > 0 ? Math.floor(element.data[element.data.length - 1].val) : 0,
  }));
  return result;
};


export const getTime = (responses) => {
  let result = [];
  if (!responses || !responses.data || !responses.data.data) {
    return result;
  }
  result = responses.data.data.map(element => ({
    name: element.valid_from,
    time: element.data.length > 0 ? Math.floor(element.data[element.data.length - 1].val) : 0,
  }));
  return result;
};
