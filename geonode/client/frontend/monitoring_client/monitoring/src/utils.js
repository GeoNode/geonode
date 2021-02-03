/*
#########################################################################
#
# Copyright (C) 2019 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
*/

import isomorphicFetch from 'isomorphic-fetch';
import { minute, hour, day, week } from './constants';


function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

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
    credentials: 'same-origin',
  };
  if (method === 'POST' || method === 'PUT' || method === 'PATCH') {
    const csrftoken = getCookie('csrftoken');
    newargs.headers['Content-Type'] = 'application/json';
    newargs.headers['X-CSRFToken'] = csrftoken;
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
  if (date === undefined) {
    return false;
  }
  const theday = `0${date.getDate()}`.slice(-2);
  const themonth = `0${date.getMonth() + 1}`.slice(-2);
  const theyear = date.getFullYear();
  const thehour = `0${date.getHours()}`.slice(-2);
  const theminute = `0${date.getMinutes()}`.slice(-2);
  const thesecond = `0${date.getSeconds()}`.slice(-2);
  return `${themonth}/${theday}/${theyear} ${thehour}:${theminute}:${thesecond}`;
};


export const sequenceInterval = (interval) => {
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
  let averageResponseTime = 0;
  let maxResponseTime = 0;
  let totalRequests = 0;

  if (!response) {
    return ["N/A", "N/A", "N/A"];
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
    if (!data.data || data.data.length === 0) {
      return [undefined, undefined, undefined];
    }
    const dataLength = data.data.length;
    if (dataLength > 0) {
      const metric = data.data[dataLength - 1];
      maxResponseTime = Number(metric.max) >= 0
                          ? Math.floor(metric.max)
                          : Number(metric.max);
      averageResponseTime = Number(metric.val) >= 0
                          ? Math.floor(metric.val)
                          : Number(metric.val);
      totalRequests = metric.samples_count;
    }
  }

  averageResponseTime = averageResponseTime > 0 ? averageResponseTime : "N/A";
  maxResponseTime = maxResponseTime > 0 ? maxResponseTime : "N/A";
  totalRequests = totalRequests > 0 ? totalRequests : "N/A";
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


export const getErrorCount = (responses) => {
  const result = 0;
  if (!responses || !responses.data || !responses.data.data) {
    return result;
  }
  return result;
};


export const formatNow = () => {
  const rightNow = new Date();
  rightNow.setSeconds(0, 0);
  return rightNow;
};


export const isNumber = (n) => {
  if (!isNaN(parseFloat(n)) && isFinite(n)) {
    return true;
  }
  return false;
};


export const stateToFields = (data) => {
  const result = [];
  Object.keys(data).forEach((fieldName) => {
    if (fieldName !== 'active' && fieldName !== 'emails') {
      result.push(fieldName);
    }
  });
  return result;
};


export const stateToData = (data) => {
  const result = {
    active: data.active,
  };
  const fields = stateToFields(data);
  fields.forEach((fieldName) => {
    if (fieldName !== 'active') {
      const field = data[fieldName];
      let value = field.current_value ? Number(field.current_value.value) : null;
      if (!field.is_enabled) {
        value = null;
      }
      result[fieldName] = value;
    }
  });
  result.emails = data.emails.split(',').map((rawEmail) => rawEmail.trim());
  return result;
};
