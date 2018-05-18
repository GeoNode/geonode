var assert = require('assert');
var strings = require('ringo/utils/strings');

const DATE_FORMAT = 'MM\'/\'dd\'/\'yyyy';
const DATE = '10/10/2010';
const URL = 'http://ringojs.org/';
const HEX_COLOR = 'd3d3d3';
const FOO = 'foo';
const NUM = '123';
const STR = "[]{}()-*+?.\\^$|#, ABC";
const ESC = "\\[\\]\\{\\}\\(\\)\\-\\*\\+\\?\\.\\\\\\^\\$\\|\\#\\,\\ ABC";
const FOO_BASE64 = 'Zm9v';
const NUM_BASE64 = 'MTIz';
const BASE16 = [
    ["pleasure", "706C656173757265"],
    ["leasure", "6C656173757265"],
    ["easure", "656173757265"],
    ["asure", "6173757265"],
    ["sure", "73757265"],
    ["\u2665", "E299A5"]
];

exports.testIsDateFormat = function () {
    assert.isTrue(strings.isDateFormat(DATE_FORMAT));
    assert.isFalse(strings.isDateFormat(FOO));
};

exports.testToDate = function () {
    var date = strings.toDate(DATE, DATE_FORMAT);
    assert.isTrue(date instanceof Date);
    assert.deepEqual(new Date(DATE), date);
    assert.throws(function () strings.toDate(FOO),
            java.lang.IllegalArgumentException); // Invalid date format.
};

exports.testIsUrl = function () {
    assert.isTrue(strings.isUrl(URL));
    assert.isFalse(strings.isUrl(FOO));
};

exports.testIsFileName = function () {
    assert.isTrue(strings.isFileName('ringo.js'));
    assert.isFalse(strings.isFileName(URL));
};

exports.testToFileName = function () {
    var fileName = strings.toFileName(URL);
    assert.isNotNull(fileName);
    assert.isTrue(strings.isFileName(fileName));
};

exports.testIsHexColor = function () {
    assert.isTrue(strings.isHexColor('#' + HEX_COLOR));
    assert.isTrue(strings.isHexColor(HEX_COLOR));
    assert.isFalse(strings.isHexColor(FOO));
};

exports.testToHexColor = function () {
    assert.strictEqual(HEX_COLOR, strings.toHexColor('rgb (211, 211, 211)'));
};

exports.testIsAlphanumeric = function () {
    assert.isTrue(strings.isAlphanumeric(FOO + NUM));
    assert.isTrue(strings.isAlphanumeric(FOO));
    assert.isFalse(strings.isAlphanumeric(URL));
};

exports.testToAlphanumeric = function () {
    var alphanumeric = strings.toAlphanumeric(URL);
    assert.isNotNull(alphanumeric);
    assert.isTrue(strings.isAlphanumeric(alphanumeric));
};

exports.testIsAlpha = function () {
    assert.isTrue(strings.isAlpha(FOO));
    assert.isFalse(strings.isAlpha(NUM));
    assert.isFalse(strings.isAlpha(NUM + FOO));
};

exports.testIsNumeric = function () {
    assert.isTrue(strings.isNumeric(NUM));
    assert.isFalse(strings.isNumeric(FOO));
    assert.isFalse(strings.isNumeric(FOO + NUM));
};

exports.testToCamelCase = function() {
    assert.strictEqual('fooBarBaz', strings.toCamelCase('foo-BAR_baz'));
    assert.strictEqual('fooBarBaz', strings.toCamelCase('foo BAR baz'));
    assert.strictEqual('fooBarBaz', strings.toCamelCase('foo\nBAR\tbaz'));
    assert.strictEqual('fooBar123baz', strings.toCamelCase('foo-bar-123baz'));
    assert.strictEqual('fooBar123Baz', strings.toCamelCase('foo-bar-123BAZ'));
    assert.strictEqual('fooBar123Baz', strings.toCamelCase('foo-bar-123-BAZ'));
};

exports.testToDashes = function() {
    assert.strictEqual('foo-bar-baz', strings.toDashes('fooBarBaz'));
};

exports.testToUnderscores = function() {
    assert.strictEqual('foo_bar_baz', strings.toUnderscores('fooBarBaz'));
};

exports.testCapitalize = function () {
    assert.strictEqual('Capitalize me.', strings.capitalize('capitalize me.'));
};

exports.testTitleize = function () {
    assert.strictEqual('Titleize Me', strings.titleize('titleize me'));
};

exports.testEntitize = function () {
    assert.strictEqual('&#102;&#111;&#111;', strings.entitize(FOO));
};

exports.testGroup = function () {
    assert.strictEqual(FOO.slice(0, 1) + NUM + FOO.slice(1, 2) + NUM + FOO.slice(2) +
            NUM, strings.group(FOO, 1, NUM));
};

exports.testUnwrap = function () {
    assert.strictEqual(FOO + FOO + FOO, strings.unwrap(FOO + '\n' + FOO, true, FOO));
};

exports.testDigest = function () {
    assert.strictEqual('ACBD18DB4CC2F85CEDEF654FCCC4A4D8', strings.digest(FOO));
};

exports.testRepeat = function () {
    assert.strictEqual(FOO, strings.repeat(FOO, 1));
    assert.strictEqual(FOO + FOO, strings.repeat(FOO, 2));
};

exports.testStartsWith = function () {
    assert.isTrue(strings.startsWith(FOO + NUM, FOO));
    assert.isFalse(strings.startsWith(NUM + FOO, FOO));
};

exports.testEndsWith = function () {
    assert.isTrue(strings.endsWith(NUM + FOO, FOO));
    assert.isFalse(strings.endsWith(FOO + NUM, FOO));
};

exports.testPad = function () { // TODO: validate behaviour resp. rework this.
    assert.strictEqual(strings.pad(FOO, NUM, 6, 1), FOO + NUM);
    assert.strictEqual(strings.pad(NUM, NUM, 4, 1), NUM + NUM.charAt(0));

    assert.strictEqual(strings.pad(FOO, NUM, 6, 0), NUM.charAt(0) + FOO + NUM.substr(0,2));
    
    assert.strictEqual(strings.pad(FOO, NUM, 6, -1), NUM + FOO);
    assert.strictEqual(strings.pad(NUM, NUM, 4, -1), NUM.charAt(0) + NUM);
};

exports.testContains = function () {
    assert.isTrue(strings.contains(FOO + NUM + FOO, NUM));
    assert.isFalse(strings.contains(FOO + FOO, NUM));
};

exports.testGetCommonPrefix = function () {
    assert.strictEqual(URL, strings.getCommonPrefix(URL + FOO, URL + NUM));
};

exports.testIsEmail = function () {
    assert.isTrue(strings.isEmail('nobody@domain.at'));
    assert.isFalse(strings.isEmail('nobody[at]domain.at'));
};

exports.testCount = function () {
    assert.strictEqual(3, strings.count(FOO + FOO + FOO, FOO));
    assert.strictEqual(3, strings.count(FOO + FOO + NUM + FOO, FOO));
};

exports.testB64Encode = function () {
    assert.strictEqual(FOO_BASE64, strings.b64encode(FOO));
    assert.strictEqual(FOO_BASE64 + NUM_BASE64, strings.b64encode(FOO + NUM));
};

exports.testB64Decode = function () {
    assert.strictEqual(FOO, strings.b64decode(FOO_BASE64));
    assert.strictEqual(FOO + NUM, strings.b64decode(FOO_BASE64 + NUM_BASE64));
};

exports.testB64EncodeDecode = function() {
    for each (var test in BASE16) {
        assert.strictEqual(strings.b16encode(test[0]), test[1]);
        assert.strictEqual(strings.b16decode(strings.b16encode(test[0])), test[0]);
        assert.deepEqual(strings.b16decode(
                strings.b16encode(test[0]), 'raw').toArray(),
                new ByteString(test[0], 'utf8').toArray());
    }
};

exports.testStripTags = function () {
    assert.strictEqual('content', strings.stripTags('<tag>content</tag>'));
};

exports.testEscapeHtml = function () {
    assert.strictEqual('&lt;p&gt;Some text.&lt;/p&gt;',
            strings.escapeHtml('<p>Some text.</p>'));
};

exports.testEscapeRegExp = function() {
    assert.equal(ESC, strings.escapeRegExp(STR));
    assert.isTrue(new RegExp(strings.escapeRegExp(STR)).test(STR));
};

exports.testSorter = function () {
    // TODO: do we really need/want this?
};

exports.testCompose = function () {
    assert.strictEqual(FOO + NUM + FOO + FOO, strings.compose(FOO, NUM, FOO, FOO));
};

exports.testRandom = function () {
    assert.isTrue(typeof strings.random() === 'string');
    assert.strictEqual(5, strings.random(5).length);
};

exports.testJoin = function () {
    assert.strictEqual(FOO + NUM, strings.join(FOO, NUM));
    assert.strictEqual(FOO + NUM + FOO, strings.join(FOO, FOO, NUM));
};

const TEMPLATE = 'Here\'s {} and {}.';
const BAR = 'bar';
const SPACE = ' ';
const NULL = 'null';
const UNDEFINED = 'undefined';
const FOO_BAR = FOO + SPACE + BAR;
const RESULT_1 = 'Here\'s ' + FOO + ' and ' + BAR + '.';
const RESULT_2 = 'Here\'s ' + SPACE + ' and ' + NUM + '.';
const RESULT_3 = 'Here\'s ' + NULL + ' and ' + UNDEFINED + '.';
const RESULT_4 = RESULT_1 + SPACE + FOO + SPACE + BAR;
const RESULT_5 = RESULT_2 + SPACE + SPACE + SPACE + NUM;
const RESULT_6 = RESULT_3 + SPACE + NULL + SPACE + UNDEFINED;

exports.testFormat = function () {
    // format string replacement
    assert.strictEqual(RESULT_1, strings.format(TEMPLATE, FOO, BAR));
    assert.strictEqual(RESULT_2, strings.format(TEMPLATE, SPACE, NUM));
    assert.strictEqual(RESULT_3, strings.format(TEMPLATE, NULL, UNDEFINED));
    // format string replacement with additional args
    assert.strictEqual(RESULT_4, strings.format(TEMPLATE, FOO, BAR, FOO, BAR));
    assert.strictEqual(RESULT_5, strings.format(TEMPLATE, SPACE, NUM, SPACE, NUM));
    assert.strictEqual(RESULT_6, strings.format(TEMPLATE, NULL, UNDEFINED, NULL, UNDEFINED));
    // no format string
    assert.strictEqual(RESULT_4, strings.format(RESULT_1, FOO, BAR));
    assert.strictEqual(RESULT_5, strings.format(RESULT_2, SPACE, NUM));
    assert.strictEqual(RESULT_6, strings.format(RESULT_3, NULL, UNDEFINED));
    // null/undefined/number as first argument
    assert.strictEqual(NULL + SPACE + FOO_BAR, strings.format(null, FOO, BAR));
    assert.strictEqual(UNDEFINED + SPACE + FOO_BAR, strings.format(undefined, FOO, BAR));
    assert.strictEqual(NUM + SPACE + FOO_BAR, strings.format(NUM, FOO, BAR));
    // null/undefined/number as last argument
    assert.strictEqual(FOO_BAR + SPACE + NULL, strings.format(FOO, BAR, null));
    assert.strictEqual(FOO_BAR + SPACE + UNDEFINED, strings.format(FOO, BAR, undefined));
    assert.strictEqual(FOO_BAR + SPACE + NUM, strings.format(FOO, BAR, NUM));
    //  null/undefined/no argument
    assert.strictEqual(NULL, strings.format(null));
    assert.strictEqual(UNDEFINED, strings.format(undefined));
    assert.strictEqual('', strings.format());
};
