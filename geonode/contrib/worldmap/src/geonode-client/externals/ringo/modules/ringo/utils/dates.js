/*
 * Copyright 1998-2005 Helma Project
 * Copyright 2010 Hannes Wallnöfer
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */

/**
 * @fileoverview Adds useful functions for working with JavaScript Date objects.
 */

var strings = require('ringo/utils/strings');

export( "format",
        "checkDate",
        "add",
        "isLeapYear",
        "before",
        "after",
        "compare",
        "firstDayOfWeek",
        "secondOfDay",
        "dayOfYear",
        "weekOfMonth",
        "weekOfYear",
        "quarterInYear",
        "quarterInFiscalYear",
        "yearInCentury",
        "daysInMonth",
        "daysInYear",
        "daysInFebruary",
        "diff",
        "overlapping",
        "inPeriod",
        "resetTime",
        "resetDate",
        "toISOString",
        "fromUTCDate",
        "parse" );

/**
 * Format a Date to a string.
 * For details on the format pattern, see
 * http://java.sun.com/j2se/1.4.2/docs/api/java/text/SimpleDateFormat.html
 *
 * @param {Date} the Date to format
 * @param {String} format the format pattern
 * @param {String|java.util.Locale} locale (optional) the locale as java Locale object or
 *        lowercase two-letter ISO-639 code (e.g. "en")
 * @param {String|java.util.TimeZone} timezone (optional) the timezone as java TimeZone
 *        object or  an abbreviation such as "PST", a full name such as "America/Los_Angeles",
 *        or a custom ID such as "GMT-8:00". If the id is not provided, the default timezone
 *        is used. If the timezone id is provided but cannot be understood, the "GMT" timezone
 *        is used.
 * @returns {String} the formatted Date
 * @see http://java.sun.com/j2se/1.4.2/docs/api/java/text/SimpleDateFormat.html
 */
function format(date, format, locale, timezone) {
    if (!format)
        return date.toString();
    if (typeof locale == "string") {
        locale = new java.util.Locale(locale);
    }
    if (typeof timezone == "string") {
        timezone = java.util.TimeZone.getTimeZone(timezone);
    }
    var sdf = locale ? new java.text.SimpleDateFormat(format, locale)
            : new java.text.SimpleDateFormat(format);
    if (timezone && timezone != sdf.getTimeZone())
        sdf.setTimeZone(timezone);
    return sdf.format(date);
}

// Helper
function createGregorianCalender(date, locale) {
    if (typeof locale == "string") {
        locale = new java.util.Locale(locale);
    }

    var cal = locale ? new java.util.GregorianCalendar(locale) : new java.util.GregorianCalendar();
    cal.set(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), date.getMinutes(), date.getSeconds());
    cal.set(java.util.Calendar.MILLISECOND, date.getMilliseconds());

    return cal;
}

/**
 * Checks if the date is a valid date. Example: 2007 is no leap year, so <tt>checkDate(2007, 1, 29)</tt> returns false.
 *
 * @param {Number} fullYear
 * @param {Number} month between 0 and 11
 * @param {Number} day between 1 and 31
 * @returns {Boolean} true, if the date is valid, false if not.
 */
function checkDate(fullYear, month, day) {
    if (fullYear == null || month == null || day == null) {
        return false;
    }

    var d = new Date(fullYear, month, day);
    return d.getFullYear() === fullYear && d.getMonth() === month && d.getDate() === day;
}

/**
 * Adds delta to the given field or reduces it, if delta is negative. If larger fields are effected,
 * they will be changed accordingly.
 *
 * @param {Date} date base date to add or remove time from.
 * @param {Number} delta amount of time to add (positive delta) or remove (negative delta).
 * @param {String} unit (optional) field to change. Possible values: <tt>year</tt>, <tt>quarter</tt>, <tt>month</tt>,
 *        <tt>week</tt>, <tt>day</tt> (default), <tt>hour</tt> (24-hour clock), <tt>minute</tt>, <tt>second</tt>,
 *        <tt>millisecond</tt>.
 * @returns {Date} date with the calculated date and time
 * @see http://download.oracle.com/javase/1.5.0/docs/api/java/util/GregorianCalendar.html#add(int,%20int)
 */
function add(date, delta, unit) {
    var cal = createGregorianCalender(date),
    delta = delta || 0,
    unit = unit || "day";

    switch (unit) {
        case "year":
            cal.add(java.util.Calendar.YEAR, delta);
            break;
        case "quarter":
            cal.add(java.util.Calendar.MONTH, delta * 3);
            break;
        case "month":
            cal.add(java.util.Calendar.MONTH, delta);
            break;
        case "week":
            cal.add(java.util.Calendar.WEEK_OF_YEAR, delta);
            break;
        case "day":
            cal.add(java.util.Calendar.DATE, delta);
            break;
        case "hour":
            cal.add(java.util.Calendar.HOUR_OF_DAY, delta);
            break;
        case "minute":
            cal.add(java.util.Calendar.MINUTE, delta);
            break;
        case "second":
            cal.add(java.util.Calendar.SECOND, delta);
            break;
        case "millisecond":
            return new Date(date.getTime() + delta);
    }
    return new Date(cal.getTimeInMillis());
}

/**
 * Checks if the date's year is a leap year.
 *
 * @param {Date} date to check year
 * @returns Boolean true if the year is a leap year, false if not.
 */
function isLeapYear(date) {
    var year = date.getFullYear();
    return year % 4 == 0 && (year % 100 != 0 || (year % 400 == 0));
}

/**
 * Checks if date <tt>a</tt> is before date <tt>b</tt>. This is equals to <tt>compareTo(a, b) &lt; 0</tt>
 *
 * @param {Date} a first date
 * @param {Date} b second date
 * @returns Boolean true if <tt>a</tt> is before <tt>b</tt>, false if not.
 */
function before(a, b) {
    return a.getTime() < b.getTime();
}

/**
 * Checks if date <tt>a</tt> is after date <tt>b</tt>. This is equals to <tt>compare(a, b) &gt; 0</tt>
 *
 * @param {Date} a first date
 * @param {Date} b second date
 * @returns Boolean true if <tt>a</tt> is after <tt>b</tt>, false if not.
 */
function after(a, b) {
    return a.getTime() > b.getTime();
}

/**
 * Compares the time values of <tt>a</tt> and <tt>b</tt>.
 *
 * @param {Date} a first date
 * @param {Date} b second date
 * @returns Number -1 if <tt>a</tt> is before <tt>b</tt>, 0 if equals and 1 if <tt>a</tt> is after <tt>b</tt>.
 * @see http://download.oracle.com/javase/1.5.0/docs/api/java/util/Calendar.html#compareTo(java.util.Calendar)
 */
function compare(a, b) {
    if (a.getTime() === b.getTime()) {
        return 0;
    } else if (a.getTime() < b.getTime()) {
        return -1;
    } else {
        return 1;
    }
}

/**
 * Gets the first day of the week.
 *
 * @param {String|java.util.Locale} locale (optional) the locale as java Locale object or
 *        lowercase two-letter ISO-639 code (e.g. "en")
 * @returns Number the first day of the week; 1 = Sunday, 2 = Monday.
 * @see http://download.oracle.com/javase/1.5.0/docs/api/constant-values.html#java.util.Calendar.SUNDAY
 */
function firstDayOfWeek(locale) {
    if (typeof locale == "string") {
        locale = new java.util.Locale(locale);
    }
    var calendar = locale ? java.util.Calendar.getInstance(locale) : java.util.Calendar.getInstance();
    return calendar.getFirstDayOfWeek();
}

/**
 * Gets the second of the day for the given date.
 * @param {Date} date calculate the second of the day.
 * @returns Number second of the day
 */
function secondOfDay(date) {
    return (date.getHours() * 3600) + (date.getMinutes() * 60) + date.getSeconds();
}

/**
 * Gets the day of the year for the given date.
 * @param {Date} date calculate the day of the year.
 * @returns Number day of the year
 */
function dayOfYear(date) {
    return createGregorianCalender(date).get(java.util.Calendar.DAY_OF_YEAR);
}

/**
 * Gets the week of the month for the given date.
 * @param {Date} date calculate the week of the month.
 * @param {String|java.util.Locale} locale (optional) the locale as java Locale object or
 *        lowercase two-letter ISO-639 code (e.g. "en")
 * @returns Number week of the month
 */
function weekOfMonth(date, locale) {
    return createGregorianCalender(date, locale).get(java.util.Calendar.WEEK_OF_MONTH);
}

/**
 * Gets the week of the year for the given date.
 * @param {Date} date calculate the week of the year.
 * @param {String|java.util.Locale} locale (optional) the locale as java Locale object or
 *        lowercase two-letter ISO-639 code (e.g. "en")
 * @returns Number week of the year
 */
function weekOfYear(date, locale) {
    return createGregorianCalender(date, locale).get(java.util.Calendar.WEEK_OF_YEAR);
}

/**
 * Gets the year of the century for the given date. <em>Examples:</em> 1900 returns 0, 2010 returns 10.
 * @param {Date} date calculate the year of the century.
 * @returns Number second of the day
 */
function yearInCentury(date) {
    var year = date.getFullYear();
    return year - (Math.floor(year / 100) * 100);
}

/**
 * Gets the number of the days in the month.
 * @param {Date} date to find the maximum number of days.
 * @returns Number days in the month, between 28 and 31.
 */
function daysInMonth(date) {
    return createGregorianCalender(date).getActualMaximum(java.util.Calendar.DAY_OF_MONTH);
}

/**
 * Gets the number of the days in the year.
 * @param {Date} date to find the maximum number of days.
 * @returns Number days in the year, 365 or 366, if it's a leap year.
 */
function daysInYear(date) {
    return isLeapYear(date) ? 366 : 365;
}

/**
 * Gets the number of the days in february.
 * @param {Date} date of year to find the number of days in february.
 * @returns Number days in the february, 28 or 29, if it's a leap year.
 */
function daysInFebruary(date) {
    return isLeapYear(date) ? 29 : 28;
}

/**
 * Gets the quarter in the year.
 * @param {Date} date to calculate the quarter for.
 * @returns Number quarter of the year, between 1 and 4.
 */
function quarterInYear(date) {
    return Math.floor((date.getMonth() / 3) + 1);
}

/**
 * Gets the quarter in the fiscal year.
 * @param {Date} date to calculate the quarter for.
 * @param {Date} fiscalYearStart first day in the fiscal year, default is the start of the current year
 * @returns Number quarter of the year, between 1 and 4.
 */
function quarterInFiscalYear(date, fiscalYearStart) {
    var firstDay   = fiscalYearStart.getDate(),
    firstMonth = fiscalYearStart.getMonth(),
    year = date.getFullYear();

    if (firstDay === 29 && firstMonth === 1) {
        throw "Fiscal year cannot start on 29th february.";
    }

    // fiscal year starts in the year before the date
    if (date.getMonth() < firstMonth || (date.getMonth() == firstMonth && date.getDate() < firstDay)) {
        year --;
    }

    var currentFiscalYear = [
        new Date(year, firstMonth, firstDay),
        new Date(year, firstMonth + 3, firstDay),
        new Date(year, firstMonth + 6, firstDay),
        new Date(year, firstMonth + 9, firstDay),
        new Date(year, firstMonth + 12, firstDay)
    ];

    for (var i = 1; i <= 4; i++) {
        if (inPeriod(date, currentFiscalYear[i-1], currentFiscalYear[i], false, true)) {
            return i;
        }
    }

    throw "Kudos! You found a bug, if you see this message. Report it!";
}

/**
 * Get the difference between two dates, specified by the unit of time.
 * @param {Date} a first date
 * @param {Date} b second date
 * @param {String} unit (optional) of time to return. Possible values: <tt>year</tt>, <tt>quarter</tt>, <tt>month</tt>,
 *        <tt>week</tt>, <tt>day</tt> (default), <tt>hour</tt>, <tt>minute</tt>, <tt>second</tt>, <tt>millisecond</tt> and
 *        <tt>mixed</tt> (returns an object)
 * @returns Number|Object<{days, hours, minutes, seconds, milliseconds}>
 *          difference between the given dates in the specified unit of time.
 */
function diff(a, b, unit) {
    var unit = unit || "day",
    mDiff = Math.abs(a.getTime() - b.getTime()),
    yDiff = Math.abs(a.getFullYear() - b.getFullYear()),
    delta = mDiff;

    switch (unit) {
        case "mixed":
            return {
                "days":           Math.floor(delta / 86400000),
                "hours":          Math.floor((delta % 86400000) / 3600000),
                "minutes":        Math.floor(((delta % 86400000) % 3600000) / 60000),
                "seconds":        Math.floor((((delta % 86400000) % 3600000) % 60000) / 1000),
                "milliseconds":   Math.floor((((delta % 86400000) % 3600000) % 60000) % 1000)
            };
        case "year":
            delta = yDiff; // just return the yDiff
            break;
        case "quarter":
            delta = (yDiff * 4) + Math.abs(quarterInYear(a) - quarterInYear(b));
            break;
        case "month":
            delta = (yDiff * 12) + Math.abs(a.getMonth() - b.getMonth());
            break;
        case "week":
            delta = Math.floor(diff(a, b, "day") / 7);
            break;
        case "day":     delta /= 24;
        case "hour":    delta /= 60;
        case "minute":  delta /= 60;
        case "second":  delta /= 1000;
                        break;
        case "millisecond": break; // delta is by default the diff in millis
    }

    return Math.floor(delta);
}

// By Dominik Gruber, written for Tenez.at
/**
 * Look if two periods are overlapping each other.
 * @param {Date} aStart first period's start
 * @param {Date} aEnd first period's end
 * @param {Date} bStart second period's start
 * @param {Date} bEnd second period's end
 * @returns Boolean true if the periods are overlapping at some point, false if not.
 */
function overlapping(aStart, aEnd, bStart, bEnd) {
    var aStart = aStart.getTime(),
        aEnd   = aEnd.getTime(),
        bStart = bStart.getTime(),
        bEnd   = bEnd.getTime();

        // A     |----|
        // B  |----|
        if(aStart >= bStart && aStart <= bEnd && aEnd >= bStart && aEnd >= bEnd) {
            return true;
        }

        // A  |----|
        // B    |----|
        if(aStart <= bStart && aStart <= bEnd && aEnd >= bStart && aEnd <= bEnd) {
            return true;
        }

        // A  |-------|
        // B    |--|
        if(aStart <= bStart && aStart <= bEnd && aEnd >= bStart && aEnd >= bEnd) {
            return true;
        }

        // A    |--|
        // B  |-------|
        if(aStart >= bStart && aStart <= bEnd && aEnd >= bStart && aEnd <= bEnd) {
            return true;
        }

        return false;
}

/**
 * Look if the date is in the period, using <em>periodStart &lt;= date &lt;= periodEnd</em>.
 * @param {Date} date to check, if it's in the period
 * @param {Date} periodStart the period's start
 * @param {Date} periodEnd the period's end
 * @param {Boolean} periodStartOpen start point is open - default false.
 * @param {Boolean} periodEndOpen end point is open - default false.
 * @returns Boolean true if the date is in the period, false if not.
 */
function inPeriod(date, periodStart, periodEnd, periodStartOpen, periodEndOpen) {
    var pStart = periodStart.getTime(),
    pEnd = periodEnd.getTime(),
    pStartOpen = periodStartOpen || false,
    pEndOpen   = periodEndOpen || false,
    dateMillis = date.getTime();

    if(!pStartOpen && !pEndOpen && pStart <= dateMillis && dateMillis <= pEnd) {
        // period  |-------|
        // date       ^
        return true;
    } else if(!pStartOpen && pEndOpen && pStart <= dateMillis && dateMillis < pEnd) {
        // period  |-------)
        // date       ^
        return true;
    } else if(pStartOpen && !pEndOpen && pStart < dateMillis && dateMillis <= pEnd) {
        // period  (-------|
        // date       ^
        return true;
    } else if(pStartOpen && pEndOpen && pStart < dateMillis && dateMillis < pEnd) {
        // period  (-------)
        // date       ^
        return true;
    }

    return false;
}

/**
 * Resets the time values to 0, keeping only year, month and day.
 * @param {Date} date to reset
 * @returns Date date without any time values
 */
function resetTime(date) {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

/**
 * Drops the date values, keeping only hours, minutes, seconds and milliseconds.
 * @param {Date} date to reset
 * @returns Date date with the original time values and 1970-01-01 as date.
 */
function resetDate(date) {
    return new Date(1970, 0, 1, date.getHours(), date.getMinutes(), date.getSeconds(), date.getMilliseconds());
}

/**
 * Create a ISO 8601 compatible string from the date. Note: This is quite similar to <tt>Date.toISOString()</tt>, which only returns
 * an UTC-based string without the local timezone. If you don't need timezones, <tt>Date.toISOString()</tt> will be the better choice.
 *
 * @param {Date} date to format
 * @param {Boolean} withTime if true, the string will contain the time, if false only the date. Default is true.
 * @param {Boolean} withTimeZone if true, the string will be in local time, if false it's in UTC. Default is true.
 * @param {Boolean} withSeconds if true, the string will contain also the seconds of the date. Default true.
 * @param {Boolean} withMilliseconds if true, the string will contain also the milliseconds of the date. Default false.
 * @returns String date as ISO 8601 string.
 */
function toISOString(date, withTime, withTimeZone, withSeconds, withMilliseconds) {
    var withTime = withTime !== false,
    withTimeZone = withTimeZone !== false,
    withSeconds = withSeconds !== false,
    withMilliseconds = withMilliseconds === true,
    year, month, day, hours, minutes, seconds, milliseconds, str;

    // use local time if output is not in UTC
    if (withTimeZone) {
        year  = date.getFullYear();
        month = date.getMonth();
        day   = date.getDate();
        hours = date.getHours();
        minutes = date.getMinutes();
        seconds = date.getSeconds();
        milliseconds = date.getMilliseconds();
    } else { // use UTC
        year  = date.getUTCFullYear();
        month = date.getUTCMonth();
        day   = date.getUTCDate();
        hours = date.getUTCHours();
        minutes = date.getUTCMinutes();
        seconds = date.getUTCSeconds();
        milliseconds = date.getUTCMilliseconds();
    }

    str = year + "-" + strings.pad((month + 1), "0", 2, -1) + "-" + strings.pad(day, "0", 2, -1);

    // Append the time
    if (withTime) {
        str += "T" + strings.pad(hours, "0", 2, -1) + ":" + strings.pad(minutes, "0", 2, -1);
        if (withSeconds) {
            str += ":" + strings.pad(seconds, "0", 2, -1);

            if (withMilliseconds) {
                str += "." + strings.pad(milliseconds, "0", 3, -1);
            }
        }
    }

    // Append the timezone offset
    if (withTime && withTimeZone) {
        var offset  = date.getTimezoneOffset(),
        inHours   = Math.floor(Math.abs(offset / 60)),
        inMinutes = Math.abs(offset) - (inHours * 60);

        // Write the time zone offset in hours
        if (offset < 0) {
            str += "+";
        } else {
            str += "-";
        }
        str += strings.pad(inHours, "0", 2, -1) + ":" + strings.pad(inMinutes, "0", 2, -1);
    } else if(withTime) {
        str += "Z"; // UTC indicator
    }

    return str;
}

/**
 * Create new Date from UTC timestamp.
 * @param {Number} year
 * @param {Number} month
 * @param {Number} date
 * @param {Number} hour
 * @param {Number} minute
 * @param {Number} second
 * @returns {Date}
 */
function fromUTCDate(year, month, date, hour, minute, second) {
    return new Date(Date.UTC(year, month, date, hour || 0 , minute || 0, second || 0));
}

/**
 * Parse a string representing a date.
 * For details on the string format, see http://tools.ietf.org/html/rfc3339.  Examples
 * include "2010", "2010-08-06", "2010-08-06T22:04:30Z", "2010-08-06T16:04:30-06".
 *
 * @param {String} str The date string.  This follows the format specified for timestamps
 *        on the internet described in RFC 3339.
 * @returns {Date} a date representing the given string
 * @see http://tools.ietf.org/html/rfc3339
 * @see http://www.w3.org/TR/NOTE-datetime
 */
function parse(str) {
    var date;
    // first check if the native parse method can parse it
    var elapsed = Date.parse(str);
    if (!isNaN(elapsed)) {
        date = new Date(elapsed);
    } else {
        var match = str.match(/^(?:(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?)?(?:T(\d{1,2}):(\d{2})(?::(\d{2}(?:\.\d+)?))?(Z|(?:[+-]\d{1,2}(?::(\d{2}))?))?)?$/);
        var date;
        if (match && (match[1] || match[7])) { // must have at least year or time
            var year = parseInt(match[1], 10) || 0;
            var month = (parseInt(match[2], 10) - 1) || 0;
            var day = parseInt(match[3], 10) || 1;

            date = new Date(Date.UTC(year, month, day));

            // Check if the given date is valid
            if (date.getUTCMonth() != month || date.getUTCDate() != day) {
                return new Date("invalid");
            }

            // optional time
            if (match[4] !== undefined) {
                var type = match[7];
                var hours = parseInt(match[4], 10);
                var minutes = parseInt(match[5], 10);
                var secFrac = parseFloat(match[6]) || 0;
                var seconds = secFrac | 0;
                var milliseconds = Math.round(1000 * (secFrac - seconds));

                // Checks if the time string is a valid time.
                var validTimeValues = function(hours, minutes, seconds) {
                    if (hours === 24) {
                        if (minutes !== 0 || seconds !== 0 || milliseconds !== 0) {
                            return false;
                        }
                    } else {
                        return false;
                    }
                    return true;
                };

                // Use UTC or local time
                if (type !== undefined) {
                    date.setUTCHours(hours, minutes, seconds, milliseconds);
                    if (date.getUTCHours() != hours || date.getUTCMinutes() != minutes || date.getUTCSeconds() != seconds) {
                        if(!validTimeValues(hours, minutes, seconds, milliseconds)) {
                            return new Date("invalid");
                        }
                    }

                    // Check offset
                    if (type !== "Z") {
                        var hoursOffset = parseInt(type, 10);
                        var minutesOffset = parseInt(match[8]) || 0;
                        var offset = -1000 * (60 * (hoursOffset * 60) + minutesOffset * 60);

                        // check maximal timezone offset (24 hours)
                        if (Math.abs(offset) >= 86400000) {
                            return new Date("invalid");
                        }
                        date = new Date(date.getTime() + offset);
                    }
                } else {
                    date.setHours(hours, minutes, seconds, milliseconds);
                    if (date.getHours() != hours || date.getMinutes() != minutes || date.getSeconds() != seconds) {
                        if(!validTimeValues(hours, minutes, seconds, milliseconds)) {
                            return new Date("invalid");
                        }
                    }
                }
            }
        } else {
            date = new Date("invalid");
        }
    }
    return date;
}
