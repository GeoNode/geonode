/**
 * @fileOverview A simple text Buffer class for composing strings.
 */

var {ByteString} = require('binary');
var strings = require('ringo/utils/strings');

export('Buffer');

/**
 * A Buffer class for composing strings. This is implemented
 * as a simple wrapper around a JavaScript array.
 * @param ... initial parts to write to the buffer
 */
function Buffer() {

    var content = [],
        length = 0;

    /**
     * Reset the buffer discarding all its content.
     * @returns this buffer object
     */
    this.reset = function() {
        content = [];
        length = 0;
        return this;
    };

    /**
     * Append all arguments to this buffer.
     * @param ... variable arguments to append to the buffer
     * @returns this buffer object
     */
    this.write = function() {
        for (var i = 0; i < arguments.length; i++) {
            var str = String(arguments[i]);
            content.push(str);
            length += str.length;
        }
        return this;
    };

    /**
     * Append all arguments to this buffer terminated by a carriage return/newline sequence.
     * @param ... variable arguments to append to the buffer
     * @returns this buffer object
     */
    this.writeln = function() {
        this.write.apply(this, arguments);
        content.push("\r\n");
        length += 2;
        return this;
    };

    /**
     * Return the content of this buffer as string.
     */
    this.toString = function() {
        return content.join('');
    };

    /**
     * Call function <code>fn</code> with each content part in this buffer.
     * @param fn a function to apply to each buffer part
     */
    this.forEach = function(fn) {
        content.forEach(fn);
    };

    /**
     * A read-only property containing the number of characters currently
     * contained by this buffer.
     */
    Object.defineProperty(this, "length", {
        get: function() { return length; }
    });
    
    /**
     * Get a message digest on the content of this buffer.
     * @param algorithm the algorithm to use, defaults to MD5
     */
    this.digest = function(algorithm) {
        var md = java.security.MessageDigest.getInstance(algorithm || "MD5");
        content.forEach(function(part) {
            md.update(String(part).toByteString());
        });
        var b = ByteString.wrap(md.digest());
        return strings.b16encode(b);
    };

    if (arguments.length > 0) {
        this.write.apply(this, arguments);
    }

    return this;
}
