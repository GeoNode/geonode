/**
 * @fileOverview A fast and extensible
 * [Markdown](http://daringfireball.net/projects/markdown/) formatter.
 */

/**
 * Converts a string of Markdown formatted text to HTML.
 *
 * Passing in an optional JavaScript object as argument allows the caller to
 * override behaviour in the markdown processor. Specifically, the following
 * methods can be overridden:
 *
 *  - __getLink(id)__ called to resolve Markdown link ids. Takes a single
 *     string id as argument and must return an array containing the target
 *     link and the target link title. If this returns null, the markdown link
 *     will not be rendered as HTML link.
 *
 *  - __openTag(tagname, buffer)__ called when a HTML tag is opened. `tagname`
 *     is an HTML tag such as `pre` or `div`, buffer is a java.lang.StringBuffer
 *     to append to. The function can be used to create HTML tags with
 *     additional attributes.
 *
 * @param {String} text a Markdown formatted text
 * @param {Object} [extension] optional object with methods overriding default
 * behaviour in org.ringojs.util.MarkdownProcessor
 * @returns {String} the Markdown text converted to HTML
 */
exports.process = function(text, extension) {
    var MarkdownProcessor = org.ringojs.util.MarkdownProcessor;
    var md = extension ? new JavaAdapter(MarkdownProcessor, extension)
                       : new MarkdownProcessor();
    return md.process(text);
}

