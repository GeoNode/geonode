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

import moment from 'moment';

let timeRangeProperties = {};

export const setTimeRangeProperties = function(properties) {
    timeRangeProperties = { ...properties };
};

export const getTimeRangeProperties = function() {
    return timeRangeProperties;
};

const getRange = function(type, intervalType, format = 'MMMM Do YYYY, h:mm:ss a', timeRangeLabel = () => '', date) {
    const today = moment.utc();
    const validTo = (date && moment.utc(date) || today.clone()).endOf(type);
    const validFrom = moment(validTo.clone()).startOf(type);
    const range = Math.round(moment(validTo.clone()).diff(validFrom.clone()) / 1000);

    const intervalFrom = moment(validTo.clone()).subtract(1, intervalType);
    const interval = Math.round(moment(validTo.clone()).diff(intervalFrom) / 1000);

    const nextDate = moment(validTo.clone()).add(1, type);
    const previousDate = moment(validFrom.clone()).subtract(1, type);
    return {
        validTo: validTo.toISOString(),
        validFrom: validFrom.toISOString(),
        range,
        format,
        interval,
        nextDate: validTo.isSameOrAfter(today) ? undefined : nextDate.toISOString(),
        previousDate: previousDate.toISOString(),
        timeRangeLabel: timeRangeLabel(validFrom, validTo)
    };
};

export const ranges = {
    day: {
        label: 'day',
        getRange: date => getRange(
            'day',
            'hour',
            'LT',
            (from, to) => `${moment(to).format('Do MMMM YYYY')}`,
            date)
    },
    week: {
        label: 'week',
        getRange: date => getRange(
            'week',
            'day',
            'ddd Do',
            (from, to) => `${moment(from).format('Do MMMM YYYY')} - ${moment(to).format('Do MMMM YYYY')}`,
            date)
    },
    month: {
        label: 'month',
        getRange: date => getRange(
            'month',
            'week',
            'Do MMM',
            (from, to) => `${moment(to).format('MMMM YYYY')}`,
            date)
    },
    year: {
        label: 'year',
        getRange: date => getRange(
            'year',
            'month',
            'MMM YYYY',
            (from, to) => `${moment(to).format('YYYY')}`,
            date)
    }
};
