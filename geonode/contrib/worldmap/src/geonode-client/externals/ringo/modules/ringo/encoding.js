/**
 * @fileOverview Low-level support for character encoding and decoding.
 */

export("Encoder", "Decoder");

var log = require("ringo/logging").getLogger(module.id);

var {Charset, CharsetEncoder, CharsetDecoder, CodingErrorAction} = java.nio.charset;
var {ByteBuffer, CharBuffer} = java.nio;
var StringUtils = org.ringojs.util.StringUtils;
var JavaString = java.lang.String;

var DEFAULTSIZE = 8192;

function Decoder(charset, strict, capacity) {

    if (!(this instanceof Decoder)) {
        return new Decoder(charset, strict, capacity);
    }

    var decoder = Charset.forName(charset).newDecoder();
    // input buffer must be able to contain any character
    capacity = Math.max(capacity, 8) || DEFAULTSIZE;
    var input = ByteBuffer.allocate(capacity);
    var output = CharBuffer.allocate(decoder.averageCharsPerByte() * capacity);
    var stream;
    var mark = 0;

    var errorAction = strict ?
            CodingErrorAction.REPORT : CodingErrorAction.REPLACE;
    decoder.onMalformedInput(errorAction);
    decoder.onUnmappableCharacter(errorAction);

    var decoded;

    /**
     * Decode bytes from the given buffer.
     * @param {binary.Binary} bytes a ByteString or ByteArray
     * @param {Number} start The start index, or 0 if undefined
     * @param {Number} end the end index, or bytes.length if undefined
     */
    this.decode = function(bytes, start, end) {
        start = start || 0;
        end = end || bytes.length;
        while (end > start) {
            var count = Math.min(end - start, input.capacity() - input.position());
            input.put(bytes, start, count);
            decodeInput(end - start);
            start += count;
        }
        decoded = null;
        return this;
    };

    /**
     * @param {Number} remaining
     */
    function decodeInput(remaining) {
        input.flip();
        var result = decoder.decode(input, output, false);
        while (result.isOverflow()) {
            // grow output buffer
            capacity += Math.max(capacity, remaining);
            var newOutput = CharBuffer.allocate(1.2 * capacity * decoder.averageCharsPerByte());
            output.flip();
            newOutput.append(output);
            output = newOutput;
            result = decoder.decode(input, output, false);
        }
        if (result.isError()) {
            decoder.reset();
            input.clear();
            throw new Error(result);
        }
        input.compact();
    }

    this.close = function() {
        input.flip();
        var result = decoder.decode(input, output, true);
        if (result.isError()) {
            decoder.reset();
            input.clear();
            throw new Error(result);
        }
        return this;
    };

    this.read = function() {
        var eof = false;
        while (stream && !eof) {
            if (mark > 0) {
                output.limit(output.position());
                output.position(mark);
                output.compact();
                mark = 0;
            }
            var position = input.position();
            var read = stream.readInto(ByteArray.wrap(input.array()), position, input.capacity());
            if (read < 0) {
                // end of stream has been reached
                eof = true;
            } else {
                input.position(position + read);
                decodeInput(0);
            }
        }
        output.flip();
        decoded = null; // invalidate
        return mark == output.limit() ?
                    null : String(output.subSequence(mark, output.limit()));
    };

    /**
     * @param {Boolean} includeNewline
     */
    this.readLine = function(includeNewline) {
        var eof = false;
        var newline = StringUtils.searchNewline(output, mark);
        while (stream && !eof && newline < 0) {
            if (mark > 0) {
                output.limit(output.position());
                output.position(mark);
                output.compact();
                mark = 0;
            }
            var position = input.position();
            var read = stream.readInto(ByteArray.wrap(input.array()), position, input.capacity());
            if (read < 0) {
                // end of stream has been reached
                eof = true;
            } else {
                var from = output.position();
                input.position(position + read);
                decodeInput(0);
                newline = StringUtils.searchNewline(output, from);
            }
        }
        output.flip();
        // get the raw underlying char[] output buffer
        var array = output.array();
        var result;
        if (newline > -1) {
            var isCrlf = array[newline] == 13 && array[newline + 1] == 10;
            if (isCrlf && includeNewline) {
                // We want to add a single newline to the return value. To save us
                // from allocating a new buffer we temporarily mod the existing one.
                array[newline] = 10;
                result = JavaString.valueOf(array, mark, newline + 1 - mark);
                array[newline] = 13;
                mark = newline + 2;
            } else {
                var count = includeNewline ? newline + 1 - mark : newline - mark;
                result = JavaString.valueOf(array, mark, count);
                mark = isCrlf ? newline + 2 : newline + 1;
            }
            output.position(output.limit());
            output.limit(output.capacity());
        } else if (eof) {
            result =  mark == output.limit() ?
                    null : JavaString.valueOf(array, mark, output.limit() - mark);
            this.clear();
        }
        decoded = null; // invalidate cached decoded representation
        return result;
    };

    this.toString = function() {
        if (decoded == null) {
            decoded = JavaString.valueOf(output.array(), mark, output.position() - mark);
        }
        return decoded;
    };

    this.hasPendingInput = function() {
        return input.position() > 0;
    };

    /**
     * @param {binary.Binary} source
     */
    this.readFrom = function(source) {
        stream = source;
        return this;
    };

    this.clear = function() {
        decoded = null;
        output.clear();
        mark = 0;
        return this;
    };

    Object.defineProperty(this, "length", {
        get: function() {
            return output.position() - mark;
        }
    });
}

function Encoder(charset, strict, capacity) {

    if (!(this instanceof Encoder)) {
        return new Encoder(charset, strict, capacity);
    }

    capacity = capacity || DEFAULTSIZE;
    var encoder = Charset.forName(charset).newEncoder();
    var encoded = new ByteArray(capacity);
    var output = ByteBuffer.wrap(encoded);
    var stream;

    var errorAction = strict ?
            CodingErrorAction.REPORT : CodingErrorAction.REPLACE;
    encoder.onMalformedInput(errorAction);
    encoder.onUnmappableCharacter(errorAction);

    /**
     * @param {String} string
     * @param {Number} start
     * @param {Number} end
     */
    this.encode = function(string, start, end) {
        start = start || 0;
        end = end || string.length;
        var input = CharBuffer.wrap(string, start, end);
        var result = encoder.encode(input, output, false);
        while (result.isOverflow()) {
            // grow output buffer
            capacity += Math.max(capacity, Math.round(1.2 * (end - start) * encoder.averageBytesPerChar()));
            encoded.length = capacity;
            var position = output.position();
            output = ByteBuffer.wrap(encoded);
            output.position(position);
            result = encoder.encode(input, output, false);
        }
        if (result.isError()) {
            encoder.reset();
            throw new Error(result);
        }
        if (stream) {
            stream.write(encoded, 0, output.position());
            // stream.flush();
            this.clear();
        }
        return this;
    };

    this.close = function() {
        var input = CharBuffer.wrap("");
        var result = encoder.encode(input, output, true);
        if (result.isError()) {
            encoder.reset();
            throw new Error(result);
        }
        if (stream) {
            stream.write(encoded, 0, output.position());
            // stream.flush();
            this.clear();
        }
        return this;
    };

    this.toString = function() {
        return "[Encoder " + output.position() + "]";
    };

    this.toByteString = function() {
        return ByteString.wrap(encoded.slice(0, output.position()));
    };

    this.toByteArray = function() {
        return encoded.slice(0, output.position());
    };

    this.writeTo = function(sink) {
        stream = sink;
        return this;
    };

    this.clear = function() {
        output.clear();
        return this;
    };

    Object.defineProperty(this, "length", {
        get: function() {
            return output.position();
        }
    });
}
