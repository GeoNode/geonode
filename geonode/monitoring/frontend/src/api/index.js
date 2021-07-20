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

import axios from 'axios';
import get from 'lodash/get';
import max from 'lodash/max';
import min from 'lodash/min';
import { ranges, getTimeRangeProperties } from '../utils/TimeRangeUtils';
import UAParser from 'ua-parser-js';
import moment from 'moment';
import countries from 'i18n-iso-countries';

// Support english language.
import countriesLangEN from 'i18n-iso-countries/langs/en.json';
countries.registerLocale(countriesLangEN);

const apiUrl = '/monitoring/api';
const uaParser = new UAParser();

const parseError = (error) => {
    const { response } = error || {};
    if (response) {
        const { status, statusText, data } = response;
        const { errors: messages } = data || {};
        return {
            status,
            statusText,
            messages
        };
    }
    return {
        status: 'UNKNOWN',
        statusText: 'UNKNOWN'
    };
};

const parseHREF = (resource) => {
    const { href } = resource || {};
    if (href) return href;
    return undefined;
};

const parseMetricsParams = function({ resourceType, eventType, resource } = {}) {
    const resourceTypeParam = resourceType !== undefined && resource === undefined && resourceType !== 'all'
        ? { resource_type: resourceType }
        : {};
    const eventTypeParam = eventType !== undefined
        ? { event_type: eventType }
        : {};
    const resourceParam = resource !== undefined
        ? { resource }
        : {};
    return {
        ...resourceTypeParam,
        ...eventTypeParam,
        ...resourceParam
    };
}

export const getUsers = () => {
    return axios.get('/api/users/')
        .then(({ data = {} } = {}) => {
            const { users = [] } = data;
            return [null, { items: users }];
        })
        .catch((e) => [parseError(e), null]);
};

export const getUsersCount = () => {
    return axios.get('/api/users/')
        .then(({ data = {} } = {}) => {
            const { users = [] } = data;
            return [null, { count: users.length }];
        })
        .catch((e) => [parseError(e), null]);
};

export const getDates = ({ resourceType = 'layers', timeRange }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`/api/${resourceType}/?limit=999999`, {
        params: {
            limit: 999999,
            date__gte: validFrom,
            date__lte: validTo
        }
    })
        .then(({ data = {} } = {}) => {
            const { objects = [] } = data;
            const obj = objects.map(({ id, name, title, owner__username, date }) => {
                return {
                    id,
                    name,
                    title,
                    owner: owner__username,
                    formatHour: moment(date).format('h:mm:ss a'),
                    date,
                    day: moment(date).format('YYYY-MM-DD')
                }
            });
            const days = obj.reduce((acc, layer) => {
                if (acc[layer.day]) {
                    return {
                        ...acc,
                        [layer.day]: [ ...acc[layer.day], layer ]
                    };
                }
                return {
                    ...acc,
                    [layer.day]: [layer]
                };
            }, {});
            const items = Object.keys(days)
                .map((date) => {
                    return {
                        date,
                        formatDate: moment(date).format('MMMM Do YYYY'),
                        count: days[date].length,
                        items: [...days[date]].reverse()
                    };
                });
            const counts = items.map(({ count }) => count);
            const dates = items.map(({ date }) => new Date(date));
            return [null, {
                items,
                minCount: min(counts),
                maxCount: max(counts),
                startDate: min(dates),
                endDate: max(dates)
            }];
        })
        .catch((e) => [parseError(e), null]);
};

export const getLayersCount = () => {
    return axios.get('/api/datasets/', {
            params: {
                limit: 1
            }
        })
        .then(({ data = {} } = {}) => {
            const { meta = {} } = data;
            const { total_count: totalCount } = meta;
            return [null, { count: totalCount || 0 }];
        })
        .catch((e) => [parseError(e), null]);
};

export const getMapsCount = () => {
    return axios.get('/api/maps/', {
            params: {
                limit: 1
            }
        })
        .then(({ data = {} } = {}) => {
            const { meta = {} } = data;
            const { total_count: totalCount } = meta;
            return [null, { count: totalCount || 0 }];
        })
        .catch((e) => [parseError(e), null]);
};

export const getDocumentsCount = () => {
    return axios.get('/api/documents/', {
            params: {
                limit: 1
            }
        })
        .then(({ data = {} } = {}) => {
            const { meta = {} } = data;
            const { total_count: totalCount } = meta;
            return [null, { count: totalCount || 0 }];
        })
        .catch((e) => [parseError(e), null]);
};


// MONITORING API

export const getServices = () => {
    return axios.get(`${apiUrl}/services/`)
        .then(({ data = {} } = {}) => {
            const { services = [] } = data;
            return [null, { services }];
        })
        .catch((e) => [parseError(e), null]);
};

export const getResourceTypes = () => {
    return axios.get(`${apiUrl}/resource_types/`)
        .then(({ data = {} } = {}) => {
            const { resource_types = [] } = data;
            return [null, {
                resourceTypes: resource_types.map((resourceType) => ({
                    ...resourceType,
                    key: resourceType.name,
                    value: resourceType.name,
                    label: resourceType.type_label || resourceType.type
                }))
            }];
        })
        .catch((e) => [parseError(e), null]);
};

export const getEventTypes = () => {
    return axios.get(`${apiUrl}/event_types/`)
        .then(({ data = {} } = {}) => {
            const { event_types = [] } = data;
            return [null, { eventTypes: event_types.map((eventType) => ({
                ...eventType,
                key: eventType.name,
                label: eventType.type_label,
                value: eventType.name })) }];
        })
        .catch((e) => [parseError(e), null]);
};

export const getResourceMainUrls = () => {
    return axios.get(`${apiUrl}/resources/?resource_type=url`)
        .then(({ data = {} } = {}) => {
            const { resources = [] } = data;
            const homeUrl = resources.find(({ name }) => name === '/') || {};
            const layersUrl = resources.find(({ name }) => name ===  '/datasets/') || {};
            return [null, { homeUrl, layersUrl }];
        })
        .catch((e) => [parseError(e), null]);
};

export const getUserAgentCount = ({ timeRange, resourceType, eventType, resource }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, range } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.ua/`, {
        params: {
            valid_from: validFrom,
            valid_to: validTo,
            interval: range,
            ...parseMetricsParams({ resourceType, eventType, resource })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data[0].data') || [])
            .map(({ val, label }) => {
                const userAgent = uaParser.setUA(label);
                return {
                    name: label,
                    count: parseFloat(val),
                    ...userAgent.getResult()
                }
            });
        return [null, { items: response }];
    })
    .catch((e) => [parseError(e), null]);
};

export const getUserAgentFamilyCount = ({ timeRange, resourceType, eventType, resource }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, range } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.ua.family/`, {
        params: {
            valid_from: validFrom,
            valid_to: validTo,
            interval: range,
            ...parseMetricsParams({ resourceType, eventType, resource })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data[0].data') || [])
            .map(({ val, label }) => ({
                name: label,
                count: parseFloat(val)
            }));
        return [null, { items: response }];
    })
    .catch((e) => [parseError(e), null]);
};

export const getCountriesCount = ({ timeRange, resourceType, eventType, resource }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, range } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.country/`, {
        params: {
            valid_from: validFrom,
            valid_to: validTo,
            interval: range,
            ...parseMetricsParams({ resourceType, eventType, resource })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data[0].data') || [])
            .map(({ val, label }) => {
                const iso2 = countries.alpha3ToAlpha2(label);
                return {
                    name: label,
                    label: countries.getName(label, 'en'),
                    flagIconClassName: iso2 && `flag-icon flag-icon-${iso2}`.toLowerCase(),
                    count: parseFloat(val)
                };
            });
        return [null, { items: response }];
    })
    .catch((e) => [parseError(e), null]);
};

/**
 * BART CHART HITS
 */
export const getResourcesHitsInterval = ({ resourceType, timeRange, resource, eventType }) => {
    const { getRange } = ranges[timeRange] || {};
    let { validFrom, validTo, interval, format } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.count`, {
        params: {
            valid_from: validFrom,
            valid_to: validTo,
            interval,
            ...parseMetricsParams({ resourceType, eventType, resource })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data') || [])
            .map(({valid_from, valid_to, data: count}) => ({
                from: valid_from,
                to: valid_to,
                val: parseFloat(get(count, '[0].val') || 0)
            }));
        const count = response.reduce((acc, { val }) => acc + (val || 0), 0);
        return [null, { items: response, count, format }];
    })
    .catch((e) => [parseError(e), null]);
};

/**
 * BART CHART VISITORS
 */
export const getResourcesVisitorsInterval = ({ resourceType, timeRange, resource, eventType }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, format, interval } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.users`, {
        params: {
            group_by: 'user',
            valid_from: validFrom,
            valid_to: validTo,
            interval: interval,
            ...parseMetricsParams({ resourceType, eventType, resource })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data') || [])
            .map(({valid_from, valid_to, data: count}) => ({
                from: valid_from,
                to: valid_to,
                val: parseFloat(get(count, '[0].val') || 0)
            }));
        const count = response.reduce((acc, { val }) => acc + (val || 0), 0);
        return [null, { items: response, count, format }];
    })
    .catch((e) => [parseError(e), null]);
};

export const getResourcesAnonymousInterval = ({ resourceType, timeRange, resource, eventType }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, format, interval } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.users`, {
        params: {
            group_by: 'label',
            user: 'AnonymousUser',
            valid_from: validFrom,
            valid_to: validTo,
            interval: interval,
            ...parseMetricsParams({ resourceType, eventType, resource })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data') || [])
            .map(({valid_from, valid_to, data: count}) => ({
                from: valid_from,
                to: valid_to,
                val: parseFloat(get(count, '[0].val') || 0)
            }));
        const count = response.reduce((acc, { val }) => acc + (val || 0), 0);
        return [null, { items: response, count, format }];
    })
    .catch((e) => [parseError(e), null]);
};

/**
 * COUNTER HITS
 */
export const getRequestHitsCount = ({ resourceType, timeRange, eventType, resource }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, range } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.count`, {
        params: {
            valid_from: validFrom,
            valid_to: validTo,
            interval: range,
            ...parseMetricsParams({ resourceType, eventType, resource })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data[0].data') || [])
            .map(({ resource = {}, val } = {}) => ({
                ...resource,
                count: parseFloat(val)
            }));
        return [null, { ...(response[0] || {}) }];
    })
    .catch((e) => [parseError(e), null]);
};

/**
 * COUNTER VISITORS
 */
export const getRequestVisitorsCount = ({ resourceType, timeRange, eventType, resource }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, range } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.users`, {
        params: {
            group_by: 'user',
            valid_from: validFrom,
            valid_to: validTo,
            interval: range,
            ...parseMetricsParams({ resourceType, eventType, resource })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data[0].data') || [])
            .map(({ resource = {}, val } = {}) => ({
                ...resource,
                count: parseFloat(val)
            }));
        return [null, { ...(response[0] || {}) }];
    })
    .catch((e) => [parseError(e), null]);
};

export const getRequestAnonymousCount = ({ resourceType, timeRange, eventType, resource }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, range } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.users`, {
        params: {
            group_by: 'label',
            user: 'AnonymousUser',
            valid_from: validFrom,
            valid_to: validTo,
            interval: range,
            ...parseMetricsParams({ resourceType, eventType, resource })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data[0].data') || [])
            .map(({ resource = {}, val } = {}) => ({
                ...resource,
                count: parseFloat(val)
            }));
        return [null, { ...(response[0] || {}) }];
    })
    .catch((e) => [parseError(e), null]);
};

export const getResourcesHitsList = ({ resourceType, timeRange, eventType }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, range } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.count`, {
        params: {
            group_by: 'resource',
            valid_from: validFrom,
            valid_to: validTo,
            interval: range,
            ...parseMetricsParams({ resourceType, eventType })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data[0].data') || [])
            .map(({ resource = {}, val } = {}) => ({
                ...resource,
                href: parseHREF(resource),
                count: parseFloat(val)
            }));
        return [null, { items: response, totalCount: response.length }];
    })
    .catch((e) => [parseError(e), null]);
};

export const getResourcesAnonymousList = ({ resourceType, timeRange, eventType }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, range } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.users`, {
        params: {
            group_by: 'resource_on_label',
            user: 'AnonymousUser',
            valid_from: validFrom,
            valid_to: validTo,
            interval: range,
            ...parseMetricsParams({ resourceType, eventType })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data[0].data') || [])
            .map(({ resource = {}, val } = {}) => ({
                ...resource,
                count: parseFloat(val)
            }));
        return [null, { items: response, totalCount: response.length }];
    })
    .catch((e) => [parseError(e), null]);
};

export const getResourcesVisitorsList = ({ resourceType, timeRange, eventType }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, range } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.users`, {
        params: {
            group_by: 'resource_on_user',
            valid_from: validFrom,
            valid_to: validTo,
            interval: range,
            ...parseMetricsParams({ resourceType, eventType })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data[0].data') || [])
            .map(({ resource = {}, val } = {}) => ({
                ...resource,
                count: parseFloat(val)
            }));
        return [null, { items: response, totalCount: response.length }];
    })
    .catch((e) => [parseError(e), null]);
};

export const getEventsHitsList = ({ resourceType, timeRange, resource }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, range } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.count`, {
        params: {
            group_by: 'event_type',
            valid_from: validFrom,
            valid_to: validTo,
            interval: range,
            ...parseMetricsParams({ resourceType, resource })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data[0].data') || [])
            .map(({ event_type, val } = {}) => ({
                name: event_type,
                id: event_type,
                count: parseFloat(val)
            }));
        return [null, { items: response, totalCount: response.length }];
    })
    .catch((e) => [parseError(e), null]);
};

export const getEventsVisitorsList = ({ resourceType, resource, timeRange }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, range } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.users`, {
        params: {
            group_by: 'event_type_on_user',
            valid_from: validFrom,
            valid_to: validTo,
            interval: range,
            ...parseMetricsParams({ resourceType, resource })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data[0].data') || [])
            .map(({ event_type, val } = {}) => ({
                name: event_type,
                id: event_type,
                count: parseFloat(val)
            }));
        return [null, { items: response, totalCount: response.length }];
    })
    .catch((e) => [parseError(e), null]);
};

export const getEventsAnonymousList = ({ resourceType, resource, timeRange }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, range } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.users`, {
        params: {
            group_by: 'event_type_on_label',
            user: 'AnonymousUser',
            valid_from: validFrom,
            valid_to: validTo,
            interval: range,
            ...parseMetricsParams({ resourceType, resource })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data[0].data') || [])
            .map(({ event_type, val } = {}) => ({
                name: event_type,
                id: event_type,
                count: parseFloat(val)
            }));
        return [null, { items: response, totalCount: response.length }];
    })
    .catch((e) => [parseError(e), null]);
};

export const getVisitorsList = ({ resourceType, resource, timeRange, eventType }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, range } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.users`, {
        params: {
            group_by: 'user_on_label',
            valid_from: validFrom,
            valid_to: validTo,
            interval: range,
            ...parseMetricsParams({ resourceType, eventType, resource })
        }
    })
    .then(({ data }) => {
        const response = (get(data, 'data.data[0].data') || [])
            .map(({ label, val, user } = {}) => ({
                id: label,
                name: user || label,
                count: parseFloat(val)
            }));
        return [null, { items: response, totalCount: response.length }];
    })
    .catch((e) => [parseError(e), null]);
};

export const getEventCountOnResource = ({ resourceType, resource, timeRange, eventType }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo, range } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.count`, {
            params: {
                group_by: 'resource',
                valid_from: validFrom,
                valid_to: validTo,
                interval: range,
                ...parseMetricsParams({ resourceType, eventType, resource })
            }
        })
        .then(({ data }) => {
            const response = (get(data, 'data.data[0].data') || [])
                .map(({ label, val, user } = {}) => ({
                    id: label,
                    name: user || label,
                    count: parseFloat(val)
                }));
            return [null, { count: response.length }];
        })
        .catch((e) => [parseError(e), null]);
};

export const getEventsDates = ({ resourceType, timeRange, eventType, resource }) => {
    const { getRange } = ranges[timeRange] || {};
    const { validFrom, validTo } = getRange && getRange() || getTimeRangeProperties();
    return axios.get(`${apiUrl}/metric_data/request.count`, {
        params: {
            group_by: 'resource',
            valid_from: validFrom,
            valid_to: validTo,
            interval: '86400', // DAY
            ...parseMetricsParams({ resourceType, eventType, resource })
        }
    })
        .then(({ data = {} } = {}) => {
                const items = (get(data, 'data.data') || [])
                    .map(({ valid_from: date, data }) => {
                        return {
                            date: moment(date).format('YYYY-MM-DD'),
                            formatDate: moment(date).format('MMMM Do YYYY'),
                            count: data.length,
                            items: data.map(({ resource = {} } = {}) => {
                                return {
                                    ...resource,
                                    title: resource.title || resource.name,
                                    formatHour: moment(date).format('h:mm:ss a')
                                };
                            })
                        };
                    });
            const counts = items.map(({ count }) => count);
            const { getRange: getYearRange } = ranges.year || {};
            const { validFrom: startDate, validTo: endDate } = getYearRange && getYearRange() || {};
            return [null, {
                items,
                minCount: min(counts),
                maxCount: max(counts),
                startDate: new Date(startDate),
                endDate: new Date(endDate)
            }];
        })
        .catch((e) => [parseError(e), null]);
};
