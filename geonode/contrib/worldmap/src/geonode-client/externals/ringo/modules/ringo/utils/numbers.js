/**
 * @fileoverview Provides utility functions for working with JavaScript numbers.
 */

export("format", "times");

/**
 * Format `number` using java.text.DecimalFormat.
 * @param {Number} number the number
 * @param {String} fmt the format to apply
 * @param {String} locale optional locale
 * @returns {String} the number formatted as string
 */
function format(number, fmt, locale) {
    var symbols;
    if (locale != null) {
        symbols = new java.text.DecimalFormatSymbols(locale);
    } else {
        symbols = new java.text.DecimalFormatSymbols();
    }
    var df = new java.text.DecimalFormat(fmt || "###,##0.##", symbols);
    return df.format(+number);
}

/**
 * Invoke a function `num` times, passing 0 .. (this - 1) as argument.
 * @param {Number} num the number
 * @param {Function} fun the function to call
 */
function times(num, fun) {
    for (var i = 0; i < num; i++) {
        fun(i);
    }
}
