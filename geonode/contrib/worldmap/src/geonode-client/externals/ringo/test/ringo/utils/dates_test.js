var assert = require('assert');
var dates = require('ringo/utils/dates');

// list of years taken from http://en.wikipedia.org/wiki/List_of_leap_years
exports.testIsLeapYear_DaysInFebruary_DaysInYear_DaysInMonth = function () {
    var leapYears = [
        1896, 1904, 1908, 1912, 1916, 1920,
        1924, 1928, 1932, 1936, 1940, 1944,
        1948, 1952, 1956, 1960, 1964, 1968,
        1972, 1976, 1980, 1984, 1988, 1992,
        1996, 2000, 2004, 2008, 2012, 2016,
        2020, 2024, 2028, 2032, 2036, 2040,
        2400, 2800
    ],
    noLeapYears = [
        1700, 1800, 1900, 2001, 2002, 2003,
        2005, 2006, 2007, 2100, 2200, 2300,
        2301, 2500, 2600, 2700, 2900, 3000,
        4003, 4005, 4007, 4009, 4011, 4317
    ];

    leapYears.forEach(function(year) {
        var d = new Date(year, 1, 1);
        assert.isTrue(dates.isLeapYear(d), "Leap Year " + year);
        assert.equal(dates.daysInYear(d), 366, "Leap Year " + year);
        assert.equal(dates.daysInFebruary(d), 29, "Leap Year " + year);
        assert.equal(dates.daysInMonth(new Date(year, 1, 1)), 29, "Leap Year " + year);
        assert.isTrue(dates.checkDate(year, 1, 29), "Leap Year " + year);
    });

    noLeapYears.forEach(function(year) {
        var d = new Date(year, 0, 1);
        assert.isFalse(dates.isLeapYear(d), "No Leap Year " + year);
        assert.equal(dates.daysInYear(d), 365, "No Leap Year " + year);
        assert.equal(dates.daysInFebruary(d), 28, "No Leap Year " + year);
        assert.equal(dates.daysInMonth(new Date(year, 1, 1)), 28, "No Leap Year " + year);
        assert.isFalse(dates.checkDate(year, 1, 29), "No Leap Year " + year);
    });
};

exports.testAdd = function () {
    var d = new Date(Date.UTC(2010, 10, 10, 10, 10, 10, 10)); // Wed Nov 10 2010 10:10:10 GMT+0100 (MEZ)

    assert.equal(d.getTime(), Date.UTC(2010, 10, 10, 10, 10, 10, 10));

    var addOne = {
        "millisecond":  Date.UTC(2010, 10, 10, 10, 10, 10, 11),
        "second":       Date.UTC(2010, 10, 10, 10, 10, 11, 10),
        "minute":       Date.UTC(2010, 10, 10, 10, 11, 10, 10),
        "hour":         Date.UTC(2010, 10, 10, 11, 10, 10, 10),
        "day":          Date.UTC(2010, 10, 11, 10, 10, 10, 10),
        "year":         Date.UTC(2011, 10, 10, 10, 10, 10, 10)
    };

    for (var tUnit in addOne) {
        assert.equal((dates.add(d, 1, tUnit)).getTime(), new Date(addOne[tUnit]).getTime(), tUnit);
    }

    // To avoid time zone and daylight saving time problems, month and quarter are tested with full circles
    assert.equal((dates.add(d, 12, "month")).getTime(), new Date(Date.UTC(2011, 10, 10, 10, 10, 10, 10)).getTime());
    assert.equal((dates.add(d, 4, "quarter")).getTime(), new Date(Date.UTC(2011, 10, 10, 10, 10, 10, 10)).getTime());

    // Add nothing
    assert.equal(dates.add(d, 0, 'millisecond').getTime(), Date.UTC(2010, 10, 10, 10, 10, 10, 10));
    assert.equal(dates.add(d, 0, 'second').getTime(), Date.UTC(2010, 10, 10, 10, 10, 10, 10));
    assert.equal(dates.add(d, 0, 'minute').getTime(), Date.UTC(2010, 10, 10, 10, 10, 10, 10));
    assert.equal(dates.add(d, 0, 'hour').getTime(), Date.UTC(2010, 10, 10, 10, 10, 10, 10));

    assert.equal(dates.add(d, 0, 'day').getTime(), Date.UTC(2010, 10, 10, 10, 10, 10, 10));
    assert.equal(dates.add(d, 0).getTime(), Date.UTC(2010, 10, 10, 10, 10, 10, 10));

    assert.equal(dates.add(d, 0, 'week').getTime(), Date.UTC(2010, 10, 10, 10, 10, 10, 10));
    assert.equal(dates.add(d, 0, 'month').getTime(), Date.UTC(2010, 10, 10, 10, 10, 10, 10));
    assert.equal(dates.add(d, 0, 'quarter').getTime(), Date.UTC(2010, 10, 10, 10, 10, 10, 10));
    assert.equal(dates.add(d, 0, 'year').getTime(), Date.UTC(2010, 10, 10, 10, 10, 10, 10));

    // Remove 1
    var removeOne = {
        "millisecond":  Date.UTC(2010, 10, 10, 10, 10, 10, 9),
        "second":       Date.UTC(2010, 10, 10, 10, 10, 9, 10),
        "minute":       Date.UTC(2010, 10, 10, 10, 9, 10, 10),
        "hour":         Date.UTC(2010, 10, 10, 9, 10, 10, 10),
        "day":          Date.UTC(2010, 10, 9, 10, 10, 10, 10),
        "year":         Date.UTC(2009, 10, 10, 10, 10, 10, 10)
    };

    for (var tUnit in removeOne) {
        assert.equal((dates.add(d, -1, tUnit)).getTime(), new Date(removeOne[tUnit]).getTime(), tUnit);
    }

    // Remove 13 hours
    var fullHourDate = new Date(Date.UTC(2010, 10, 10, 23, 10, 10, 10)); // Wed Nov 10 2010 23:10:10 GMT+0100 (MEZ)
    assert.equal(dates.add(fullHourDate, -13, 'hour').getTime(), Date.UTC(2010, 10, 10, 10, 10, 10, 10));
    
    // Add 13 hours
    fullHourDate = new Date(Date.UTC(2010, 10, 10, 0, 10, 10, 10)); // Wed Nov 10 2010 00:10:10 GMT+0100 (MEZ)
    assert.equal(dates.add(fullHourDate, 13, 'hour').getTime(), Date.UTC(2010, 10, 10, 13, 10, 10, 10));
    
    // Remove 48 hours
    assert.equal(dates.add(d, -48, 'hour').getTime(), Date.UTC(2010, 10, 8, 10, 10, 10, 10));
    
    // Add 48 hours
    assert.equal(dates.add(d, 48, 'hour').getTime(), Date.UTC(2010, 10, 12, 10, 10, 10, 10));
    
    // Add 61 hours
    assert.equal(dates.add(d, 61, 'hour').getTime(), Date.UTC(2010, 10, 12, 23, 10, 10, 10));
    
    // Remove 61 hours
    assert.equal(dates.add(d, -61, 'hour').getTime(), Date.UTC(2010, 10, 7, 21, 10, 10, 10));

    // To avoid time zone and daylight saving time problems, month and quarter are tested with full circles
    assert.equal((dates.add(d, -12, "month")).getTime(), new Date(Date.UTC(2009, 10, 10, 10, 10, 10, 10)).getTime());
    assert.equal((dates.add(d, -4, "quarter")).getTime(), new Date(Date.UTC(2009, 10, 10, 10, 10, 10, 10)).getTime());

    // Use time zone and daylight saving time "save" calculations for week
    d = new Date(Date.UTC(2010, 11, 31, 0, 0, 0, 0))
    assert.equal((dates.add(d, -1, "week")).getTime(), new Date(Date.UTC(2010, 11, 24, 0, 0, 0, 0)).getTime());

    d = new Date(Date.UTC(2010, 11, 24, 0, 0, 0, 0))
    assert.equal((dates.add(d, 1, "week")).getTime(), new Date(Date.UTC(2010, 11, 31, 0, 0, 0, 0)).getTime());
};

exports.testBefore_After_Compare = function () {
    var a = new Date(2010, 0, 2), b = new Date(2010, 0, 1);

    assert.isFalse(dates.before(a, b));
    assert.isTrue(dates.after(a, b));
    assert.equal(dates.compare(a, b), 1);

    a = new Date(2010, 0, 1);
    b = new Date(2010, 0, 2);
    assert.isTrue(dates.before(a, b));
    assert.isFalse(dates.after(a, b));
    assert.equal(dates.compare(a, b), -1);

    a = new Date(2010, 0, 1);
    b = new Date(2010, 0, 1);
    assert.isFalse(dates.before(a, b));
    assert.isFalse(dates.after(a, b));
    assert.equal(dates.compare(a, b), 0);

    a = new Date(2008, 1, 29);
    b = new Date(2008, 1, 29);
    assert.isFalse(dates.before(a, b));
    assert.isFalse(dates.after(a, b));
    assert.equal(dates.compare(a, b), 0);

    a = new Date(2000, 1, 29);
    b = new Date(2008, 1, 29);
    assert.isTrue(dates.before(a, b));
    assert.isFalse(dates.after(a, b));
    assert.equal(dates.compare(a, b), -1);
};

exports.testFirstDayOfWeek = function () {
    assert.equal(dates.firstDayOfWeek("de"), 2);
    assert.equal(dates.firstDayOfWeek("us"), 1);

    assert.equal(dates.firstDayOfWeek(java.util.Locale.GERMANY), 2);
    assert.equal(dates.firstDayOfWeek(java.util.Locale.US), 1);
};

exports.testQuarterInYear = function() {
    assert.equal(dates.quarterInYear(new Date(2010, 0, 1)), 1);
    assert.equal(dates.quarterInYear(new Date(2010, 3, 1)), 2);
    assert.equal(dates.quarterInYear(new Date(2010, 6, 1)), 3);
    assert.equal(dates.quarterInYear(new Date(2010, 9, 1)), 4);

    assert.equal(dates.quarterInYear(new Date(2010, 1, 1)), 1);
    assert.equal(dates.quarterInYear(new Date(2010, 4, 1)), 2);
    assert.equal(dates.quarterInYear(new Date(2010, 7, 1)), 3);
    assert.equal(dates.quarterInYear(new Date(2010, 10, 1)), 4);

    assert.equal(dates.quarterInYear(new Date(2010, 2, 1)), 1);
    assert.equal(dates.quarterInYear(new Date(2010, 5, 1)), 2);
    assert.equal(dates.quarterInYear(new Date(2010, 8, 1)), 3);
    assert.equal(dates.quarterInYear(new Date(2010, 11, 1)), 4);

    assert.equal(dates.quarterInYear(new Date(2010, 2, 31)), 1);
    assert.equal(dates.quarterInYear(new Date(2010, 5, 30)), 2);
    assert.equal(dates.quarterInYear(new Date(2010, 8, 30)), 3);
    assert.equal(dates.quarterInYear(new Date(2010, 11, 31)), 4);
}

exports.testQuarterInFiscalYear = function() {
    // UK tax year
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 0, 6), new Date(1990, 3, 6)), 4);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 3, 6), new Date(1990, 3, 6)), 1);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 6, 6), new Date(1990, 3, 6)), 2);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 9, 6), new Date(1990, 3, 6)), 3);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 3, 5, 23, 59, 59), new Date(1990, 3, 6)), 4);

    // With standard year starting on 01/01
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 0, 1), new Date(1970, 0, 1)), 1);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 3, 1), new Date(1970, 0, 1)), 2);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 6, 1), new Date(1970, 0, 1)), 3);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 9, 1), new Date(1970, 0, 1)), 4);

    assert.equal(dates.quarterInFiscalYear(new Date(2010, 1, 1), new Date(1970, 0, 1)), 1);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 4, 1), new Date(1970, 0, 1)), 2);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 7, 1), new Date(1970, 0, 1)), 3);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 10, 1), new Date(1970, 0, 1)), 4);

    assert.equal(dates.quarterInFiscalYear(new Date(2010, 2, 1), new Date(1970, 0, 1)), 1);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 5, 1), new Date(1970, 0, 1)), 2);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 8, 1), new Date(1970, 0, 1)), 3);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 11, 1), new Date(1970, 0, 1)), 4);

    assert.equal(dates.quarterInFiscalYear(new Date(2010, 2, 31), new Date(1970, 0, 1)), 1);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 5, 30), new Date(1970, 0, 1)), 2);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 8, 30), new Date(1970, 0, 1)), 3);
    assert.equal(dates.quarterInFiscalYear(new Date(2010, 11, 31), new Date(1970, 0, 1)), 4);
};

exports.testDiff = function() {
    var a = new Date(2010, 0, 1),
    b = new Date(2010, 0, 2);

    assert.equal(dates.diff(a, b, "year"), 0);
    assert.equal(dates.diff(a, b, "quarter"), 0);
    assert.equal(dates.diff(a, b, "month"), 0);
    assert.equal(dates.diff(a, b, "week"), 0);
    assert.equal(dates.diff(a, b, "day"), 1);
    assert.equal(dates.diff(a, b, "hour"), 24);
    assert.equal(dates.diff(a, b, "minute"), 1440);
    assert.equal(dates.diff(a, b, "second"), 86400);
    assert.equal(dates.diff(a, b, "millisecond"), 86400000);
    assert.deepEqual(dates.diff(a, b, "mixed"), {
        "days": 1,
        "hours": 0,
        "minutes": 0,
        "seconds": 0,
        "milliseconds": 0
    });

    // normal year
    b = new Date(2009, 0, 1);
    assert.equal(dates.diff(a, b, "year"), 1);
    assert.equal(dates.diff(a, b, "quarter"), 4);
    assert.equal(dates.diff(a, b, "month"), 12);
    assert.equal(dates.diff(a, b, "week"), 52);
    assert.equal(dates.diff(a, b, "day"), 365);
    assert.equal(dates.diff(a, b, "hour"), 8760);
    assert.equal(dates.diff(a, b, "minute"), 525600);
    assert.equal(dates.diff(a, b, "second"), 31536000);
    assert.equal(dates.diff(a, b, "millisecond"), 31536000000);
    assert.deepEqual(dates.diff(a, b, "mixed"), {
        "days": 365,
        "hours": 0,
        "minutes": 0,
        "seconds": 0,
        "milliseconds": 0
    });

    // leap year
    a = new Date(2012, 0, 1);
    b = new Date(2013, 0, 1);
    assert.equal(dates.diff(a, b, "year"), 1);
    assert.equal(dates.diff(a, b, "quarter"), 4);
    assert.equal(dates.diff(a, b, "month"), 12);
    assert.equal(dates.diff(a, b, "week"), 52);
    assert.equal(dates.diff(a, b, "day"), 366);
    assert.equal(dates.diff(a, b, "hour"), 8784);
    assert.equal(dates.diff(a, b, "minute"), 527040);
    assert.equal(dates.diff(a, b, "second"), 31622400);
    assert.equal(dates.diff(a, b, "millisecond"), 31622400000);
    assert.deepEqual(dates.diff(a, b, "mixed"), {
        "days": 366,
        "hours": 0,
        "minutes": 0,
        "seconds": 0,
        "milliseconds": 0
    });

    // one minute
    a = new Date(2012, 0, 1, 0, 1);
    b = new Date(2012, 0, 1, 0, 2);
    assert.equal(dates.diff(a, b, "year"), 0);
    assert.equal(dates.diff(a, b, "quarter"), 0);
    assert.equal(dates.diff(a, b, "month"), 0);
    assert.equal(dates.diff(a, b, "week"), 0);
    assert.equal(dates.diff(a, b, "day"), 0);
    assert.equal(dates.diff(a, b, "hour"), 0);
    assert.equal(dates.diff(a, b, "minute"), 1);
    assert.equal(dates.diff(a, b, "second"), 60);
    assert.equal(dates.diff(a, b, "millisecond"), 60000);
    assert.deepEqual(dates.diff(a, b, "mixed"), {
        "days": 0,
        "hours": 0,
        "minutes": 1,
        "seconds": 0,
        "milliseconds": 0
    });

    // one millisecond
    a = new Date(1234567890);
    b = new Date(1234567891);
    assert.equal(dates.diff(a, b, "year"), 0);
    assert.equal(dates.diff(a, b, "quarter"), 0);
    assert.equal(dates.diff(a, b, "month"), 0);
    assert.equal(dates.diff(a, b, "week"), 0);
    assert.equal(dates.diff(a, b, "day"), 0);
    assert.equal(dates.diff(a, b, "hour"), 0);
    assert.equal(dates.diff(a, b, "minute"), 0);
    assert.equal(dates.diff(a, b, "second"), 0);
    assert.equal(dates.diff(a, b, "millisecond"), 1);
    assert.deepEqual(dates.diff(a, b, "mixed"), {
        "days": 0,
        "hours": 0,
        "minutes": 0,
        "seconds": 0,
        "milliseconds": 1
    });

    // more tests (Einstein's life)
    a = new Date(1879, 2, 14);
    b = new Date(1955, 3, 18);
    assert.equal(dates.diff(a, b, "year"), 76);
    assert.equal(dates.diff(a, b, "quarter"), 305);
    assert.equal(dates.diff(a, b, "month"), 913);
    assert.equal(dates.diff(a, b, "week"), 3970);
    assert.equal(dates.diff(a, b, "day"), 27793);

    // again Einstein, now with time diff
    b = new Date(1955, 3, 18, 20, 39, 10, 53);
    assert.equal(dates.diff(a, b, "year"), 76);
    assert.equal(dates.diff(a, b, "quarter"), 305);
    assert.equal(dates.diff(a, b, "month"), 913);
    assert.equal(dates.diff(a, b, "week"), 3970);
    assert.equal(dates.diff(a, b, "day"), 27793);
};

exports.testOverlapping = function() {
    var aStart = new Date(2010, 0, 1),
    aEnd = new Date(2010, 0, 10),
    bStart = new Date(2010, 0, 2),
    bEnd = new Date(2010, 0, 3);

    // A  |-------|
    // B    |--|
    assert.isTrue(dates.overlapping(aStart, aEnd, bStart, bEnd));

    // A    |-------|
    // B |----|
    bStart = new Date(2009, 0, 1);
    assert.isTrue(dates.overlapping(aStart, aEnd, bStart, bEnd));

    // A    |-----|
    // B |-----------|
    bStart = new Date(2009, 0, 1);
    bEnd   = new Date(2010, 0, 11);
    assert.isTrue(dates.overlapping(aStart, aEnd, bStart, bEnd));

    // A |-------|
    // B   |--------|
    bStart = new Date(2010, 0, 2);
    bEnd   = new Date(2010, 0, 11);
    assert.isTrue(dates.overlapping(aStart, aEnd, bStart, bEnd));

    // A |----|
    // B      |----|
    bStart = new Date(2010, 0, 10);
    bEnd   = new Date(2010, 0, 13);
    assert.isTrue(dates.overlapping(aStart, aEnd, bStart, bEnd));

    // A       |----|
    // B  |----|
    bStart = new Date(2009, 0, 1);
    bEnd   = new Date(2010, 0, 1);
    assert.isTrue(dates.overlapping(aStart, aEnd, bStart, bEnd));

    // A |----|
    // B        |----|
    bStart = new Date(2010, 0, 11);
    bEnd   = new Date(2010, 0, 13);
    assert.isFalse(dates.overlapping(aStart, aEnd, bStart, bEnd));
};

exports.testInPeriod = function() {
    var pStart = new Date(2010, 0, 10),
    pEnd = new Date(2010, 0, 20);

    //  Period   [--------]
    //  Date     ^
    assert.isTrue(dates.inPeriod(new Date(2010, 0, 10), pStart, pEnd, false, false));

    //  Period   (--------]
    //  Date     ^
    assert.isFalse(dates.inPeriod(new Date(2010, 0, 10), pStart, pEnd, true, false));

    //  Period   [--------]
    //  Date              ^
    assert.isTrue(dates.inPeriod(new Date(2010, 0, 20), pStart, pEnd, false, false));

    //  Period   [--------)
    //  Date              ^
    assert.isFalse(dates.inPeriod(new Date(2010, 0, 20), pStart, pEnd, false, true));

    //  Period   [--------]
    //  Date         ^
    assert.isTrue(dates.inPeriod(new Date(2010, 0, 15), pStart, pEnd, false, false));

    //  Period   (--------)
    //  Date         ^
    assert.isTrue(dates.inPeriod(new Date(2010, 0, 15), pStart, pEnd, true, true));

    //  Period   [--------]
    //  Date                 ^
    assert.isFalse(dates.inPeriod(new Date(2010, 0, 22), pStart, pEnd, false, false));

    //  Period     [--------]
    //  Date    ^
    assert.isFalse(dates.inPeriod(new Date(2010, 0, 5), pStart, pEnd, false, false));

    //  Period   (--------)
    //  Date                 ^
    assert.isFalse(dates.inPeriod(new Date(2010, 0, 22), pStart, pEnd, true, true));

    //  Period     (--------)
    //  Date    ^
    assert.isFalse(dates.inPeriod(new Date(2010, 0, 5), pStart, pEnd, true, true));

    //  Period   (--------]
    //  Date                 ^
    assert.isFalse(dates.inPeriod(new Date(2010, 0, 22), pStart, pEnd, true, false));

    //  Period     [--------)
    //  Date    ^
    assert.isFalse(dates.inPeriod(new Date(2010, 0, 5), pStart, pEnd, false, true));
};

exports.testResetTime = function() {
    var d = new Date(2010, 0, 1, 20, 20, 20);
    assert.equal(dates.resetTime(d).getFullYear(), 2010);
    assert.equal(dates.resetTime(d).getMonth(), 0);
    assert.equal(dates.resetTime(d).getDate(), 1);
    assert.equal(dates.resetTime(d).getHours(), 0);
    assert.equal(dates.resetTime(d).getMinutes(), 0);
    assert.equal(dates.resetTime(d).getSeconds(), 0);
};

exports.testResetDate = function() {
    var d = new Date(2010, 0, 1, 20, 20, 20);
    assert.equal(dates.resetDate(d).getFullYear(), 1970);
    assert.equal(dates.resetDate(d).getMonth(), 0);
    assert.equal(dates.resetDate(d).getDate(), 1);
    assert.equal(dates.resetDate(d).getHours(), 20);
    assert.equal(dates.resetDate(d).getMinutes(), 20);
    assert.equal(dates.resetDate(d).getSeconds(), 20);
};

exports.testSecondsOfDay = function() {
    assert.equal(dates.secondOfDay(new Date(1970, 0, 1, 0, 0, 0)), 0);
    assert.equal(dates.secondOfDay(new Date(1970, 0, 1, 0, 1, 0)), 60);
    assert.equal(dates.secondOfDay(new Date(1970, 0, 1, 1, 0, 0)), 3600);
    assert.equal(dates.secondOfDay(new Date(1970, 0, 2, 0, 0, 0)), 0);
};

exports.testDayOfYear = function() {
    assert.equal(dates.dayOfYear(new Date(1970, 0, 1, 0, 0, 0)), 1);
    assert.equal(dates.dayOfYear(new Date(1970, 0, 1, 0, 1, 0)), 1);
    assert.equal(dates.dayOfYear(new Date(1970, 0, 1, 1, 0, 0)), 1);
    assert.equal(dates.dayOfYear(new Date(1970, 0, 2, 0, 0, 0)), 2);
    assert.equal(dates.dayOfYear(new Date(2010, 11, 31, 0, 0, 0)), 365);
    // leap year
    assert.equal(dates.dayOfYear(new Date(2000, 1, 29, 0, 0, 0)), 60);
    assert.equal(dates.dayOfYear(new Date(2000, 11, 31, 0, 0, 0)), 366);
};

exports.testWeekOfMonth = function() {
    assert.equal(dates.weekOfMonth(new Date(2011, 0, 1), "de"), 0);
    assert.equal(dates.weekOfMonth(new Date(2011, 0, 31), "de"), 5);
    assert.equal(dates.weekOfMonth(new Date(2011, 1, 1), "de"), 1);
    assert.equal(dates.weekOfMonth(new Date(2011, 1, 28), "de"), 5);
    assert.equal(dates.weekOfMonth(new Date(2010, 4, 31), "de"), 5);

    // Additional check for different locales
    assert.equal(dates.weekOfMonth(new Date(2011, 0, 1), "us"), 1);
    assert.equal(dates.weekOfMonth(new Date(2011, 0, 31), "us"), 6);
    assert.equal(dates.weekOfMonth(new Date(2011, 0, 1), java.util.Locale.US), 1);
    assert.equal(dates.weekOfMonth(new Date(2011, 0, 31), java.util.Locale.US), 6);
};

exports.testWeekOfYear = function() {
    assert.equal(dates.weekOfYear(new Date(2010, 0, 1), "de"), 53);
    assert.equal(dates.weekOfYear(new Date(2010, 0, 4), "de"), 1);
    assert.equal(dates.weekOfYear(new Date(2010, 11, 31), "de"), 52);

    assert.equal(dates.weekOfYear(new Date(2011, 0, 1), "de"), 52);
    assert.equal(dates.weekOfYear(new Date(2011, 0, 3), "de"), 1);
    assert.equal(dates.weekOfYear(new Date(2011, 11, 31), "de"), 52);

    assert.equal(dates.weekOfYear(new Date(2012, 0, 1), "de"), 52);
    assert.equal(dates.weekOfYear(new Date(2012, 0, 3), "de"), 1);
    assert.equal(dates.weekOfYear(new Date(2012, 11, 31), "de"), 1);

    // Additional check for different locales
    assert.equal(dates.weekOfYear(new Date(2012, 0, 1), java.util.Locale.US), 1);
    assert.equal(dates.weekOfYear(new Date(2012, 0, 1), java.util.Locale.GERMANY), 52);
    assert.equal(dates.weekOfYear(new Date(2012, 0, 1), "us"), 1);
    assert.equal(dates.weekOfYear(new Date(2012, 0, 1), "de"), 52);
};

exports.testYearInCentury = function() {
    assert.equal(dates.yearInCentury(new Date(1000, 0, 1)), 0);
    assert.equal(dates.yearInCentury(new Date(1900, 0, 1)), 0);
    assert.equal(dates.yearInCentury(new Date(2000, 0, 1)), 0);
    assert.equal(dates.yearInCentury(new Date(2010, 0, 1)), 10);
    assert.equal(dates.yearInCentury(new Date(2022, 0, 1)), 22);
};

exports.testDaysInMonth = function() {
    assert.equal(dates.daysInMonth(new Date(2010, 0, 1)), 31); // Jan
    assert.equal(dates.daysInMonth(new Date(2010, 1, 1)), 28); // Feb
    assert.equal(dates.daysInMonth(new Date(2010, 2, 1)), 31); // Mar
    assert.equal(dates.daysInMonth(new Date(2010, 3, 1)), 30); // Apr
    assert.equal(dates.daysInMonth(new Date(2010, 4, 1)), 31); // May
    assert.equal(dates.daysInMonth(new Date(2010, 5, 1)), 30); // Jun
    assert.equal(dates.daysInMonth(new Date(2010, 6, 1)), 31); // Jul
    assert.equal(dates.daysInMonth(new Date(2010, 7, 1)), 31); // Aug
    assert.equal(dates.daysInMonth(new Date(2010, 8, 1)), 30); // Sep
    assert.equal(dates.daysInMonth(new Date(2010, 9, 1)), 31); // Oct
    assert.equal(dates.daysInMonth(new Date(2010, 10, 1)), 30); // Nov
    assert.equal(dates.daysInMonth(new Date(2010, 11, 1)), 31); // Dec

    // Leap Year
    assert.equal(dates.daysInMonth(new Date(2008, 1, 1)), 29); // Feb
};

exports.testFromUTCDate = function() {
    var d = dates.fromUTCDate(1970, 0, 1, 0, 0, 0);
    assert.equal(d.getUTCFullYear(), 1970);
    assert.equal(d.getUTCMonth(), 0);
    assert.equal(d.getUTCDate(), 1);
    assert.equal(d.getUTCHours(), 0);
    assert.equal(d.getUTCMinutes(), 0);
    assert.equal(d.getUTCSeconds(), 0);
    assert.equal(d.getTime(), 0);
};

exports.testCheckDate = function() {
    assert.isTrue(dates.checkDate(2008, 1, 28));
    assert.isTrue(dates.checkDate(2008, 1, 29));

    assert.isTrue(dates.checkDate(2010, 0, 31));
    assert.isTrue(dates.checkDate(2010, 1, 28));
    assert.isTrue(dates.checkDate(2010, 2, 31));
    assert.isTrue(dates.checkDate(2010, 3, 30));
    assert.isTrue(dates.checkDate(2010, 4, 31));
    assert.isTrue(dates.checkDate(2010, 5, 30));
    assert.isTrue(dates.checkDate(2010, 6, 31));
    assert.isTrue(dates.checkDate(2010, 7, 31));
    assert.isTrue(dates.checkDate(2010, 8, 30));
    assert.isTrue(dates.checkDate(2010, 9, 31));
    assert.isTrue(dates.checkDate(2010, 10, 30));
    assert.isTrue(dates.checkDate(2010, 11, 31));

    assert.isFalse(dates.checkDate(2010, 1, 29));
    assert.isFalse(dates.checkDate("a", "b", "c"));
    assert.isFalse(dates.checkDate(2010, "b", "c"));
    assert.isFalse(dates.checkDate("a", 2, "c"));
    assert.isFalse(dates.checkDate("a", "b", 2));
};

exports.testParse = function() {
    // Check for same time: http://www.w3.org/TR/NOTE-datetime
    assert.strictEqual(dates.parse("1994-11-05T08:15:30-05:00").getTime(), dates.parse("1994-11-05T13:15:30Z").getTime());

    assert.strictEqual((dates.parse("2009-02-13T23:31:30Z")).getTime(), 1234567890000); // GMT: Fri, 13 Feb 2009 23:31:30 GMT
    assert.strictEqual((dates.parse("2009-02-13T23:31:30+00:00")).getTime(), 1234567890000); // GMT: Fri, 13 Feb 2009 23:31:30 GMT
    assert.strictEqual((dates.parse("2010-01-01T00:00+01:00")).getTime(), 1262300400000);
    assert.strictEqual((dates.parse("2010-10-26T00:00+02:00")).getTime(), 1288044000000);
    assert.strictEqual((dates.parse("2010-10-26T00:00:00+02:00")).getTime(), 1288044000000);
    assert.strictEqual((dates.parse("2010-10-26T00:00:00.0+02:00")).getTime(), 1288044000000);
    assert.strictEqual((dates.parse("2010-10-26T00:00:00.00+02:00")).getTime(), 1288044000000);
    assert.strictEqual((dates.parse("2010-10-26T00:00:00.000+02:00")).getTime(), 1288044000000);

    // UTC
    assert.strictEqual((dates.parse("2010-10-26T00:00Z")).getTime(), 1288051200000);
    assert.strictEqual((dates.parse("2010-10-26T00:00:00Z")).getTime(), 1288051200000);
    assert.strictEqual((dates.parse("2010-10-26T00:00:00.0Z")).getTime(), 1288051200000);
    assert.strictEqual((dates.parse("2010-10-26T00:00:00.00Z")).getTime(), 1288051200000);
    assert.strictEqual((dates.parse("2010-10-26T00:00:00.000Z")).getTime(), 1288051200000);

    // NaN
    assert.isNaN(dates.parse("asdf"));
    assert.isNaN(dates.parse("2010-"));
    assert.isNaN(dates.parse("2010-99"));
    assert.isNaN(dates.parse("2010-01-99"));
    assert.isNaN(dates.parse("2010-01-01T24:59Z"));
    assert.isNaN(dates.parse("2010-01-01T25:00Z"));
    assert.isNaN(dates.parse("2010-01-01TT25:00Z"));
    assert.isNaN(dates.parse("2010-01-01T23:00-25:00"));

    // Check for not NaN
    // FIXME no exact checks because of local time...
    assert.isNotNaN(dates.parse("2010-01-01T01:01").getTime());
    assert.isNotNaN(dates.parse("2010-01-01T01:01:01").getTime());
    assert.isNotNaN(dates.parse("2010-01-01T01:01:01.001").getTime());

    // cases map datestrings to objects with corresponding UTC date properties
    var cases = {
        "2000": {
            year: 2000,
            month: 0,
            date: 1
        },
        "2005-10": {
            year: 2005,
            month: 9,
            date: 1
        },
        "1971-07-23": {
            year: 1971,
            month: 6,
            date: 23
        },
        "1801-11-20T04:30:15Z": {
            year: 1801,
            month: 10,
            date: 20,
            hour: 4,
            minutes: 30,
            seconds: 15
        },
        "1989-06-15T18:30:15.91Z": {
            year: 1989,
            month: 5,
            date: 15,
            hour: 18,
            minutes: 30,
            seconds: 15,
            milliseconds: 910
        },
        "1989-06-15T18:30:15.9105Z": {
            year: 1989,
            month: 5,
            date: 15,
            hour: 18,
            minutes: 30,
            seconds: 15,
            milliseconds: 911
        },
        "2010-01-01T00:00:00+01:00": { // zero hour
            year: 2009,
            month: 11,
            date: 31,
            hour: 23,
            minutes: 0,
            seconds: 0
        },
        "2010-01-01T24:00Z": { // 24:00
            year: 2010,
            month: 0,
            date: 2,
            hour: 0,
            minutes: 0,
            seconds: 0
        },
        "2010-01-01T00:00+01:00": { // no seconds (lenient)
            year: 2009,
            month: 11,
            date: 31,
            hour: 23,
            minutes: 0,
            seconds: 0
        },
        "2010-08-06T15:21:25-06": { // MDT
            year: 2010,
            month: 7,
            date: 6,
            hour: 21,
            minutes: 21,
            seconds: 25
        },
        "2010-08-07T06:21:25+9": { // JSP
            year: 2010,
            month: 7,
            date: 6,
            hour: 21,
            minutes: 21,
            seconds: 25
        },
        "2010-08-07T02:51:25+05:30": { // IST
            year: 2010,
            month: 7,
            date: 6,
            hour: 21,
            minutes: 21,
            seconds: 25
        },
        "T18:30:15.91Z": {
            hour: 18,
            minutes: 30,
            seconds: 15,
            milliseconds: 910
        },
        "T21:51:25Z": {
            hour: 21,
            minutes: 51,
            seconds: 25
        },
        "T02:51:25+05:30": { // IST
            hour: 21,
            minutes: 21,
            seconds: 25
        },
        "T2:51:25.1234-7": { // lenient
            hour: 9,
            minutes: 51,
            seconds: 25,
            milliseconds: 123
        }
    };

    var o, got, exp;
    for (var str in cases) {
        o = cases[str];
        got = dates.parse(str);
        exp = new Date(Date.UTC(o.year || 0, o.month || 0, o.date || 1, o.hour || 0, o.minutes || 0, o.seconds || 0, o.milliseconds || 0));
        if ("year" in o) {
            assert.strictEqual(got.getUTCFullYear(), exp.getUTCFullYear(), str + ": correct UTCFullYear");
            assert.strictEqual(got.getUTCMonth(), exp.getUTCMonth(), str + ": correct UTCMonth");
            assert.strictEqual(got.getUTCDate(), exp.getUTCDate(), str + ": correct UTCDate");
        }
        assert.strictEqual(got.getUTCHours(), exp.getUTCHours(), str + ": correct UTCHours");
        assert.strictEqual(got.getUTCMinutes(), exp.getUTCMinutes(), str + ": correct UTCMinutes");
        assert.strictEqual(got.getUTCSeconds(), exp.getUTCSeconds(), str + ": correct UTCSeconds");
        assert.strictEqual(got.getUTCMilliseconds(), exp.getUTCMilliseconds(), str + ": correct UTCMilliseconds");
    }

    return;
};

exports.testToISOString = function() {
    var d = new Date(Date.UTC(2010, 0, 2, 2, 3, 4, 5));
    assert.strictEqual(dates.toISOString(d, false, false), "2010-01-02");
    assert.strictEqual(dates.toISOString(d, true, false, false), "2010-01-02T02:03Z");
    assert.strictEqual(dates.toISOString(d, true, false, true), "2010-01-02T02:03:04Z");
    assert.strictEqual(dates.toISOString(d, true, false, true, true), "2010-01-02T02:03:04.005Z");

    d = new Date(Date.UTC(2010, 0, 2, 12, 0, 0, 0));
    assert.strictEqual(dates.toISOString(d, true, false, true), "2010-01-02T12:00:00Z");
    assert.strictEqual(dates.toISOString(d, true, false, true, true), "2010-01-02T12:00:00.000Z");

    // Test for local time using current time to prevent nasty timzone/dst jumps
    d = new Date();
    var sdf = new java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssZ");
    var formatted = sdf.format(d);
    assert.strictEqual(dates.toISOString(d, true, true), formatted.substr(0,22) + ":" + formatted.substr(-2));
    
    sdf = new java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSZ");
    formatted = sdf.format(d);
    assert.strictEqual(dates.toISOString(d, true, true, true, true), formatted.substr(0,26) + ":" + formatted.substr(-2));;
};

if (require.main == module.id) {
    require("test").run(exports);
}
