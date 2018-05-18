/**
 * @fileoverview <p>This module implements the Stream/TextStream classes as per
 * the <a href="http://wiki.commonjs.org/wiki/IO/A">CommonJS IO/A</a>
 * proposal.</p>
 */

var {Binary, ByteArray, ByteString} = require("binary");
var {Encoder, Decoder} = require("ringo/encoding");

defineClass(org.ringojs.wrappers.Stream);

/**
 * This class implements an I/O stream used to read and write raw bytes.
 * @constructor
 */
exports.Stream = Stream;

/** @ignore provides Narwhal compatibility */
exports.IO = Stream;

var {InputStreamReader, BufferedReader, OutputStreamWriter, BufferedWriter} = java.io;

/**
 * Reads all data available from this stream and writes the result to the
 * given output stream, flushing afterwards. Note that this function does
 * not close this stream or the output stream after copying.
 * @param {Stream} output The target Stream to be written to.
 */
Stream.prototype.copy = function(output) {
    var read, length = 8192;
    var buffer = new ByteArray(length);
    while ((read = this.readInto(buffer, 0, length)) > -1) {
        output.write(buffer, 0, read);
    }
    output.flush();
    return this;
};

/**
 * Read all data from this stream and invoke function `fn` for each chunk of data read.
 * The callback function is called with a ByteArray as single argument. Note that
 * the stream is not closed after reading.
 * @param {Function} fn the callback function
 * @param {Object} [thisObj] optional this-object to use for callback
 */
Stream.prototype.forEach = function(fn, thisObj) {
    var read, length = 8192;
    var buffer = new ByteArray(length);
    while ((read = this.readInto(buffer, 0, length)) > -1) {
        buffer.length = read;
        fn.call(thisObj, buffer);
        buffer.length = length;
    }
};

/**
 * A binary stream that reads from and/or writes to an in-memory byte array.
 *
 * If the constructor is called with a Number argument, a ByteArray with the
 * given length is allocated and the length of the stream is set to zero.
 *
 * If the argument is a [binary object][binary] it will be used as underlying
 * buffer and the stream length set to the length of the binary object.
 * If argument is a [ByteArray][binary#ByteArray], the resulting stream is both
 * readable, writable, and seekable. If it is a [ByteString][binary#ByteString],
 * the resulting stream is readable and seekable but not writable.
 *
 * If called without argument, a ByteArray of length 1024 is allocated as buffer.
 *
 * @param {Binary|Number} binaryOrNumber the buffer to use, or the initial
 * capacity of the buffer to allocate.
 * @constructor
 */
exports.MemoryStream = function MemoryStream(binaryOrNumber) {

    var buffer, length;
    if (!binaryOrNumber) {
        buffer = new ByteArray(0);
        length = 0;
    } else if (binaryOrNumber instanceof Binary) {
        buffer = binaryOrNumber;
        length = buffer.length;
    } else if (typeof binaryOrNumber == "number") {
        buffer = new ByteArray(binaryOrNumber);
        length = 0;
    } else {
        throw new Error("Argument must be Binary, Number, or undefined");
    }

    var stream = Object.create(Stream.prototype);
    var position = 0;
    var closed = false;
    var canWrite = buffer instanceof ByteArray;

    function checkClosed() {
        if (closed) {
            throw new Error("Stream has been closed");
        }
    }

    /**
     * Returns true if the stream supports reading, false otherwise.
     * Always returns true for MemoryStreams.
     * @name MemoryStream.prototype.readable
     * @see #Stream.prototype.readable
     * @return {Boolean} true if stream is readable
     * @function
     */
    stream.readable = function() {
       return true;
    };

    /**
     * Returns true if the stream supports writing, false otherwise.
     * For MemoryStreams this returns true if the wrapped binary is an
     * instance of ByteArray.
     * @name MemoryStream.prototype.writable
     * @see #Stream.prototype.writable
     * @return {Boolean} true if stream is writable
     * @function
     */
    stream.writable = function() {
        return buffer instanceof ByteArray;
    };

    /**
     * Returns true if the stream is randomly accessible and supports the length
     * and position properties, false otherwise.
     * Always returns true for MemoryStreams.
     * @name MemoryStream.prototype.seekable
     * @see #Stream.prototype.seekable
     * @return {Boolean} true if stream is seekable
     * @function
     */
    stream.seekable = function() {
        return true;
    };

    /**
     * Read up to `maxBytes` bytes from the stream, or until the end of the stream
     * has been reached. If `maxBytes` is not specified, the full stream is read
     * until its end is reached. Reading from a stream where the end has already been
     * reached returns an empty ByteString.
     * @name MemoryStream.prototype.read
     * @param {Number} maxBytes the maximum number of bytes to read
     * @returns {ByteString}
     * @see #Stream.prototype.read
     * @function
     */
    stream.read = function(maxBytes) {
        checkClosed();
        var result;
        if (isFinite(maxBytes)) {
            if (maxBytes < 0) {
                throw new Error("read(): argument must not be negative");
            }
            var end = Math.min(position + maxBytes, length);
            result = ByteString.wrap(buffer.slice(position, end));
            position = end;
            return result;
        } else {
            result = ByteString.wrap(buffer.slice(position, length));
            position = length;
        }
        return result;
    };

    /**
     * Read bytes from this stream into the given buffer. This method does
     * *not* increase the length of the buffer.
     * @name MemoryStream.prototype.readInto
     * @param {ByteArray} buffer the buffer
     * @param {Number} begin optional begin index, defaults to 0.
     * @param {Number} end optional end index, defaults to buffer.length - 1.
     * @returns {Number} The number of bytes read or -1 if the end of the stream
     *          has been reached
     * @see #Stream.prototype.readInto
     * @function
     */
    stream.readInto = function(target, begin, end) {
        checkClosed();
        if (!(target instanceof ByteArray)) {
            throw new Error("readInto(): first argument must be ByteArray");
        }
        if (position >= length) {
            return -1;
        }
        begin = begin === undefined ? 0 : Math.max(0, begin);
        end = end === undefined ? target.length : Math.min(target.length, end);
        if (begin < 0 || end < 0) {
            throw new Error("readInto(): begin and end must not be negative");
        } else if (begin > end) {
            throw new Error("readInto(): end must be greater than begin");
        }
        var count = Math.min(length - position, end - begin);
        buffer.copy(position, position + count, target, begin);
        position += count;
        return count;
    };

    /**
     * Write bytes from b to this stream. If begin and end are specified,
     * only the range starting at begin and ending before end is written.
     * @name MemoryStream.prototype.write
     * @param {Binary} source The source to be written from
     * @param {Number} begin optional
     * @param {Number} end optional
     * @see #Stream.prototype.write
     * @function
     */
    stream.write = function(source, begin, end) {
        checkClosed();
        if (typeof source === "string") {
            system.stderr.print("Warning: binary write called with string argument. "
                    + "Using default encoding");
            source = source.toByteString();
        }
        if (!(source instanceof Binary)) {
            throw new Error("write(): first argument must be binary");
        }
        begin = begin === undefined ? 0 : Math.max(0, begin);
        end = end === undefined ? source.length : Math.min(source.length, end);
        if (begin > end) {
            throw new Error("write(): end must be greater than begin");
        }
        var count = end - begin;
        source.copy(begin, end, buffer, position);
        position += count;
        length = Math.max(length, position);
    };

    /**
     * The wrapped buffer.
     * @name MemoryStream.prototype.content
     */
    Object.defineProperty(stream, "content", {
        get: function() {
            return buffer;
        }
    });

    /**
     * The number of bytes in the stream's underlying buffer.
     * @name MemoryStream.prototype.length
     */
    Object.defineProperty(stream, "length", {
        get: function() {
            checkClosed();
            return length
        },
        set: function(value) {
            if (canWrite) {
                checkClosed();
                length = buffer.length = value;
                position = Math.min(position, length);
            }
        }
    });

    /**
     * The current position of this stream in the wrapped buffer.
     * @name MemoryStream.prototype.position
     */
    Object.defineProperty(stream, "position", {
        get: function() {
            checkClosed();
            return position;
        },
        set: function(value) {
            checkClosed();
            position = Math.min(Math.max(0, value), length);
        }
    });

    /**
     * Try to skip over num bytes in the stream. Returns the number of acutal bytes skipped
     * or throws an error if the operation could not be completed.
     * @name Stream.prototype.skip
     * @param {Number} num bytes to skip
     * @returns {Number} actual bytes skipped
     * @name MemoryStream.prototype.skip
     * @function
     */
    stream.skip = function(num) {
        checkClosed();
        num = Math.min(parseInt(num, 10), length - position);
        if (isNaN(num)) {
            throw new Error("skip() requires a number argument");
        } else if (num < 0) {
            throw new Error("Argument to skip() must not be negative");
        }
        position += num;
        return num
    };

    /**
     * Flushes the bytes written to the stream to the underlying medium.
     * @name MemoryStream.prototype.flush
     * @function
     */
    stream.flush = function() {
        checkClosed();
    };

    /**
     * Closes the stream, freeing the resources it is holding.
     * @name MemoryStream.prototype.close
     * @function
     */
    stream.close = function() {
        checkClosed();
        closed = true;
    };

    /**
     * Returns true if the stream is closed, false otherwise.
     * @name MemoryStream.prototype.closed
     * @return {Boolean} true if the stream has been closed
     * @function
     */
    stream.closed = function() {
        return closed;
    };

    return stream;
};

/**
 * A TextStream implements an I/O stream used to read and write strings. It
 * wraps a raw Stream and exposes a similar interface.
 * @param {Stream} io The raw Stream to be wrapped.
 * @param {Object} options the options object. Supports the following properties:
 *        <ul><li>charset: string containing the name of the encoding to use.
 *            Defaults to "utf8".</li>
 *        <li>newline: string containing the newline character sequence to use.
 *            Defaults to "\n".</li>
 *        <li>delimiter: string containing the delimiter to use in print().
 *            Defaults to " ".</li></ul>
 * @param {number} buflen optional buffer size. Defaults to 8192.
 * @constructor
 */
exports.TextStream = function TextStream(io, options, buflen) {
    if (this.constructor !== exports.TextStream) {
        return new exports.TextStream(io, options, buflen);
    }

    options = options || {};
    var charset = options.charset || "utf8";
    var newline = options.hasOwnProperty("newline") ? options.newline : "\n";
    var delimiter = options.hasOwnProperty("delimiter") ? options.delimiter : " ";
    var reader, writer;
    var encoder, decoder;
    var DEFAULTSIZE = 8192;

    if (io.readable()) {
        decoder = new Decoder(charset, false, buflen || DEFAULTSIZE);
        decoder.readFrom(io);
    }

    if (io.writable()) {
        encoder = new Encoder(charset, false, buflen || DEFAULTSIZE);
        encoder.writeTo(io);
    }

    /**
     * @see #Stream.prototype.readable
     */
    this.readable = function() {
       return io.readable();
    };

    /**
     * @see #Stream.prototype.writable
     */
    this.writable = function() {
        return io.writable();
    };

    /**
     * Always returns false, as a TextStream is not randomly accessible.
     */
    this.seekable = function() {
        return false;
    };

    /**
     * Reads a line from this stream. If the end of the stream is reached
     * before any data is gathered, returns an empty string. Otherwise, returns
     * the line including the newline.
     * @returns {String} the next line
     */
    this.readLine = function () {
        var line = decoder.readLine(true);
        if (line === null)
            return "";
        return String(line);
    };

    /**
     * Returns this stream.
     * @return {TextStream} this stream
     */
    this.iterator = function () {
        return this;
    };

    /**
     * Returns the next line of input without the newline. Throws
     * `StopIteration` if the end of the stream is reached.
     * @returns {String} the next line
     */
    this.next = function () {
        var line = decoder.readLine(false);
        if (line == null) {
            throw StopIteration;
        }
        return String(line);
    };
    
    /**
     * Calls `callback` with each line in the input stream.
     * @param {Function} callback the callback function
     * @param {Object} [thisObj] optional this-object to use for callback
     */
    this.forEach = function (callback, thisObj) {
        var line = decoder.readLine(false);
        while (line != null) {
            callback.call(thisObj, line);
            line = decoder.readLine(false);
        }
    };

    /**
     * Returns an Array of Strings, accumulated by calling `readLine` until it
     * returns an empty string. The returned array does not include the final
     * empty string, but it does include a trailing newline at the end of every
     * line.
     * @returns {Array} an array of lines
     */
    this.readLines = function () {
        var lines = [];
        do {
            var line = this.readLine();
            if (line.length)
                lines.push(line);
        } while (line.length);
        return lines;
    };

    /**
     * Read the full stream until the end is reached and return the data read
     * as string.
     * @returns {String}
     */
    this.read = function () {
        return decoder.read();
    };

    /**
     * Not implemented for TextStraim. Calling this method will raise an error.
     */
    this.readInto = function (buffer) {
        throw new Error("Not implemented");
    };

    /**
     * Reads from this stream with [readLine][#readLine], writing the results
     * to the target stream and flushing, until the end of this stream is reached.
     */
    this.copy = function (output) {
        while (true) {
            var line = this.readLine();
            if (!line.length)
                break;
            output.write(line).flush();
        }
        return this;
    };

    /**
     * Writes all arguments to the stream.
     */
    this.write = function () {
        for (var i = 0; i < arguments.length; i++) {
            encoder.encode(String(arguments[i]));
        }
        return this;
    };

    /**
     * Writes the given line to the stream, followed by a newline.
     */
    this.writeLine = function (line) {
        this.write(line + newline);
        return this;
    };

    /**
     * Writes the given lines to the stream, terminating each line with a newline.
     *
     * This is a non-standard extension, not part of CommonJS IO/A.
     */
    this.writeLines = function (lines) {
        lines.forEach(this.writeLine, this);
        return this;
    };

    /**
     * Writes all argument values as a single line, delimiting the values using
     * a single blank.
     */
    this.print = function () {
        for (var i = 0; i < arguments.length; i++) {
            this.write(String(arguments[i]));
            if (i < arguments.length - 1) {
                this.write(delimiter);
            }
        }
        this.write(newline);
        this.flush();
        return this;
    };

    /**
     * @see #Stream.prototype.flush
     */
    this.flush = function () {
        io.flush();
        return this;
    };

    /**
     * @see #Stream.prototype.close
     */
    this.close = function () {
        io.close();
    };

    /**
     * If the wrapped stream is a [MemoryStream][#MemoryStream] this contains its
     * content decoded to a String with this streams encoding. Otherwise contains
     * an empty String.
     */
    Object.defineProperty(this, "content", {
        get: function() {
            var wrappedContent = io.content;
            if (!wrappedContent) {
                return "";
            }
            return wrappedContent.decodeToString(charset);
        }
    });

    /**
     * The wrapped binary stream.
     */
    Object.defineProperty(this, "raw", {
        get: function() {
            return io;
        }
    });

    return this;
};

/**
 * Write bytes from b to this stream. If begin and end are specified, only the
 * range starting at begin and ending before end is written.
 * @name Stream.prototype.write
 * @param {Binary} source The source to be written from
 * @param {Number} begin optional
 * @param {Number} end optional
 * @function
 */

/**
 * Read up to `maxBytes` bytes from the stream, or until the end of the stream
 * has been reached. If `maxBytes` is not specified, the full stream is read
 * until its end is reached. Reading from a stream where the end has already been
 * reached returns an empty ByteString.
 * @name Stream.prototype.read
 * @param {Number} maxBytes the maximum number of bytes to read
 * @returns {ByteString}
 * @function
 */

/**
 * Read bytes from this stream into the given buffer. This method does
 * *not* increase the length of the buffer.
 * @name Stream.prototype.readInto
 * @param {ByteArray} buffer the buffer
 * @param {Number} begin optional begin index, defaults to 0.
 * @param {Number} end optional end index, defaults to buffer.length - 1.
 * @returns {Number} The number of bytes read or -1 if the end of the stream
 *          has been reached
 * @function
 */

/**
 * Try to skip over num bytes in the stream. Returns the number of acutal bytes skipped
 * or throws an error if the operation could not be completed.
 * @name Stream.prototype.skip
 * @param {Number} num bytes to skip
 * @returns {Number} actual bytes skipped
 * @function
 */

/**
 * Flushes the bytes written to the stream to the underlying medium.
 * @name Stream.prototype.flush
 * @function
 */

/**
 * Closes the stream, freeing the resources it is holding.
 * @name Stream.prototype.close
 * @function
 */

/**
 * Returns true if the stream has been closed, false otherwise.
 * @name Stream.prototype.closed
 * @return {Boolean} true if the stream has been closed
 * @function
 */

/**
 * Returns true if the stream supports reading, false otherwise.
 * @name Stream.prototype.readable
 * @return {Boolean} true if stream is readable
 * @function
 */

/**
 * Returns true if the stream is randomly accessible and supports the length
 * and position properties, false otherwise.
 * @name Stream.prototype.seekable
 * @return {Boolean} true if stream is seekable
 * @function
 */

/**
 * Returns true if the stream supports writing, false otherwise.
 * @name Stream.prototype.writable
 * @return {Boolean} true if stream is writable
 * @function
 */

/**
 * Get the Java input or output stream instance wrapped by this Stream.
 * @name Stream.prototype.unwrap
 * @function
 */

/**
 * The wrapped `java.io.InputStream`.
 * @name Stream.prototype.inputStream
 * @property
 * @type java.io.InputStream
 */

/**
 * The wrapped `java.io.OutputStream`.
 * @name Stream.prototype.outputStream
 * @property
 * @type java.io.OutputStream
 */
